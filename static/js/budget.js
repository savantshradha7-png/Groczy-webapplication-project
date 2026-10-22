(()=>{
  const app=document.getElementById('budget-app');
  const amount=document.getElementById('budget-amount');
  const category=document.getElementById('budget-category');
  const preference=document.getElementById('budget-preference');
  const errorBox=document.getElementById('budget-error');
  const results=document.getElementById('budget-results');
  const loading=document.getElementById('budget-loading');
  const itemsBox=document.getElementById('budget-items');
  const emptyBox=document.getElementById('budget-empty');
  const storageKey='groczy-budget-list-v1';
  let state=null, variant=0;
  const fmt=n=>'₹'+Number(n||0).toFixed(2);
  const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const decimal=n=>Math.round((Number(n)+Number.EPSILON)*100)/100;
  function save(){if(state)sessionStorage.setItem(storageKey,JSON.stringify(state));else sessionStorage.removeItem(storageKey)}
  function selectedTotal(){return decimal((state?.items||[]).filter(i=>i.selected).reduce((sum,i)=>sum+Number(i.unit_price)*i.quantity,0))}
  function showError(message){errorBox.textContent=message;errorBox.classList.remove('d-none')}
  function hideError(){errorBox.textContent='';errorBox.classList.add('d-none')}
  function render(){
    if(!state)return;
    results.classList.remove('d-none');
    const hasItems=state.items.length>0;
    emptyBox.classList.toggle('d-none',hasItems);
    itemsBox.classList.toggle('d-none',!hasItems);
    document.getElementById('budget-summary').classList.toggle('d-none',!hasItems);
    document.getElementById('budget-empty-message').textContent=state.message||'Try increasing the budget or choosing another category.';
    itemsBox.innerHTML=state.items.map(item=>`<article class="budget-item" data-product-id="${item.product_id}"><label class="budget-select"><input type="checkbox" data-action="select" ${item.selected?'checked':''} aria-label="Select ${esc(item.name)}"></label><img src="${esc(item.image_url||'https://placehold.co/180x150/e8f5e9/198754?text=Grocery')}" alt="${esc(item.name)}" onerror="this.src='https://placehold.co/180x150/e8f5e9/198754?text=Grocery'"><div class="budget-item-details"><span class="eyebrow">${esc(item.category)}</span><h3>${esc(item.name)}</h3><span class="budget-unit-price">${fmt(item.unit_price)} each · ${item.stock} in stock</span><div class="budget-quantity"><label>Quantity <input type="number" min="1" max="${item.stock}" value="${item.quantity}" data-action="quantity" aria-label="Quantity for ${esc(item.name)}"></label><button type="button" class="budget-remove" data-action="remove">Remove</button></div></div><strong class="budget-line-total">${fmt(Number(item.unit_price)*item.quantity)}</strong></article>`).join('');
    const total=selectedTotal(), budget=Number(state.budget);
    document.getElementById('budget-total').textContent=fmt(total);
    document.getElementById('budget-remaining').textContent=fmt(Math.max(0,decimal(budget-total)));
    const addButton=document.getElementById('budget-add-cart');
    addButton.disabled=!state.items.some(i=>i.selected);
    document.getElementById('budget-cart-message').textContent=app.dataset.authenticated==='1'?'':'Sign in to add the selected list to your saved cart.';
    save();
  }
  async function generate(regenerate=false){
    hideError();loading.classList.remove('d-none');results.classList.add('d-none');
    const raw=amount.value;
    if(!raw||!Number.isFinite(Number(raw))||Number(raw)<=0||Number(raw)>100000){loading.classList.add('d-none');showError('Enter a budget greater than ₹0 and no more than ₹100,000.');return}
    if(regenerate)variant++;
    const body={budget:raw,category:category.value,preference:preference.value,variant};
    if(regenerate&&state?.items?.length)body.exclude_ids=state.items.map(i=>i.product_id);
    try{
      const data=await api('/api/budget/generate',{method:'POST',body:JSON.stringify(body)});
      state={budget:data.budget,items:data.items.map(i=>({...i,selected:true})),message:data.message||''};
      render();
    }catch(e){showError(e.message)}
    finally{loading.classList.add('d-none')}
  }
  itemsBox.addEventListener('change',e=>{
    const row=e.target.closest('.budget-item');if(!row||!state)return;
    const id=Number(row.dataset.productId),item=state.items.find(i=>i.product_id===id);if(!item)return;
    if(e.target.dataset.action==='select')item.selected=e.target.checked;
    if(e.target.dataset.action==='quantity'){
      const next=Number(e.target.value),current=item.quantity;
      if(!Number.isInteger(next)||next<1||next>item.stock){showError(`Choose a quantity between 1 and ${item.stock}.`);e.target.value=current;return}
      item.quantity=next;
      if(selectedTotal()>Number(state.budget)){item.quantity=current;e.target.value=current;showError('That quantity would exceed your budget. Reduce the quantity or remove another selected item.');return}
    }
    hideError();render();
  });
  itemsBox.addEventListener('click',e=>{
    if(e.target.dataset.action!=='remove')return;
    const row=e.target.closest('.budget-item'),id=Number(row.dataset.productId);
    state.items=state.items.filter(i=>i.product_id!==id);render();
  });
  document.querySelectorAll('[data-budget]').forEach(button=>button.addEventListener('click',()=>{amount.value=button.dataset.budget;amount.focus()}));
  document.getElementById('generate-budget').addEventListener('click',()=>generate(false));
  document.getElementById('regenerate-budget').addEventListener('click',()=>generate(true));
  document.getElementById('budget-add-cart').addEventListener('click',async()=>{
    if(!state)return;
    const selected=state.items.filter(i=>i.selected).map(i=>({product_id:i.product_id,quantity:i.quantity}));
    if(!selected.length){showError('Select at least one product first.');return}
    const total=selectedTotal();
    if(total>Number(state.budget)){showError('The selected list exceeds your budget. Adjust it before adding to cart.');return}
    if(app.dataset.authenticated!=='1'){save();location.href='/login?next=%2Fbudget-shopping';return}
    hideError();const button=document.getElementById('budget-add-cart');button.disabled=true;button.textContent='Adding items…';
    try{await api('/api/budget/add-to-cart',{method:'POST',body:JSON.stringify({budget:state.budget,items:selected})});sessionStorage.removeItem(storageKey);location.href='/cart'}
    catch(e){showError(e.message);button.disabled=false;button.innerHTML='<i class="fa-solid fa-cart-plus me-2"></i>Add Selected Items to Cart'}
  });
  try{const saved=sessionStorage.getItem(storageKey);if(saved){state=JSON.parse(saved);amount.value=state.budget;render()}}catch{sessionStorage.removeItem(storageKey)}
})();
