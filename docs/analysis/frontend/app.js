/* Local frontend concept. No credentials, remote requests or production API. */
'use strict';
const $ = selector => document.querySelector(selector);
const escapeHTML = value => String(value).replace(/[&<>"']/g, character => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[character]));
const normalize = value => value.trim().toLowerCase();
const clock = () => new Date().toISOString();
const date = value => new Date(value).toLocaleDateString('en-GB',{day:'numeric',month:'short'});
const recipeFixtures = [
  {id:'sample-skillet',title:'Tomato & rice skillet',ingredients:['rice','tomato','onion'],steps:['Rinse the rice and set it aside.','Soften the chopped onion in a pan, then add the tomatoes.','Stir in the rice with water and simmer until cooked.'],cookingMinutes:25,caloriesPerServing:380,servings:2,description:'A simple, comforting skillet for the ingredients you already have.'},
  {id:'sample-bowl',title:'Spinach rice bowl',ingredients:['rice','spinach','lemon'],steps:['Cook the rice until tender.','Wilt the spinach gently in a warm pan.','Serve over rice with a squeeze of lemon.'],cookingMinutes:20,caloriesPerServing:325,servings:2,description:'A bright little bowl that makes an everyday meal feel fresh.'}
];
let state, generationTimer, toastTimer, modalRecipeId;
function seed() {
  clearTimeout(generationTimer);
  state={route:'fridge',signedIn:true,expired:false,inventory:[{id:'i1',name:'Rice',addedAt:'2026-10-12T09:00:00Z'},{id:'i2',name:'Tomato',addedAt:'2026-10-13T09:00:00Z'},{id:'i3',name:'Spinach',addedAt:'2026-10-14T09:00:00Z'}],shopping:[],preferences:{dietary:['Vegetarian'],allergens:[]},recipes:[],favorites:new Set(),history:new Map(),savedTab:'favorites',generation:'idle',forceError:false,nextId:10};
}
const bowl = () => `<svg viewBox="0 0 280 215" role="img" aria-label="Illustration of a bowl of rice and vegetables"><ellipse cx="141" cy="186" rx="92" ry="12" fill="#b9cdb1" opacity=".55"/><path d="M44 91h192c-3 65-29 98-96 98S48 156 44 91" fill="#f8f6e8"/><path d="M49 112c14 53 42 72 92 72 49 0 80-23 88-72" fill="none" stroke="#d7d7bc" stroke-width="3"/><ellipse cx="140" cy="91" rx="97" ry="44" fill="#305a42"/><ellipse cx="140" cy="88" rx="88" ry="35" fill="#ded8af"/><g fill="#f3edcc"><ellipse cx="111" cy="89" rx="39" ry="21"/><ellipse cx="147" cy="74" rx="35" ry="19"/><ellipse cx="160" cy="94" rx="38" ry="20"/></g><g fill="#72945a"><ellipse cx="84" cy="68" rx="14" ry="24" transform="rotate(-40 84 68)"/><ellipse cx="99" cy="57" rx="13" ry="23" transform="rotate(-19 99 57)"/><ellipse cx="187" cy="81" rx="15" ry="26" transform="rotate(40 187 81)"/><ellipse cx="176" cy="62" rx="12" ry="22" transform="rotate(16 176 62)"/></g><g fill="#cf6a43" stroke="#b65134" stroke-width="2"><circle cx="105" cy="104" r="15"/><circle cx="166" cy="93" r="13"/><circle cx="132" cy="63" r="11"/></g><g fill="#f2c46b"><circle cx="121" cy="81" r="4"/><circle cx="144" cy="108" r="4"/><circle cx="153" cy="63" r="4"/><circle cx="73" cy="91" r="4"/></g><path d="M203 53l34-39" stroke="#977b4c" stroke-width="8" stroke-linecap="round"/></svg>`;
const icons = name => ({rice:'◒',tomato:'●',spinach:'❧',onion:'◉',lemon:'◐'}[normalize(name)] || '✳');
function announce(message) { $('#announcement').textContent=message;$('#announcement').classList.add('visible');clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('#announcement').classList.remove('visible'),4500); }
function heading(kicker,title,description,count='') { return `<div class="page-heading"><div><p class="section-kicker">${kicker}</p><h1>${title}</h1><p>${description}</p></div>${count?`<span class="counter">${count}</span>`:''}</div>`; }
function empty(title,description,action='',symbol='✳') { return `<div class="empty-state"><span class="empty-icon" aria-hidden="true">${symbol}</span><h2>${title}</h2><p>${description}</p>${action}</div>`; }
function inputForm(kind,label,placeholder) { return `<form class="inline-form" id="${kind}-form" novalidate><div class="field"><label for="${kind}-name">${label}</label><input id="${kind}-name" name="name" autocomplete="off" placeholder="${placeholder}" aria-describedby="${kind}-error"></div><button class="btn btn-primary" type="submit"><span aria-hidden="true">＋</span> Add</button></form><p id="${kind}-error" class="field-error form-error hide" role="alert"></p>`; }
function inventory() {
  return heading('A FRESH START','Your fridge, full of possibilities.','Keep track of what you have. Find something lovely to make.',`${state.inventory.length} ingredients at home`)+
  `<section class="hero" aria-labelledby="hero-title"><div><p class="section-kicker">LESS GUESSING. MORE COOKING.</p><h2 id="hero-title">Your next good meal<br>is already taking shape.</h2><p>Turn a few everyday ingredients into a recipe worth making.</p><button class="btn btn-primary" data-action="generate">Find recipes <span aria-hidden="true">↗</span></button></div><div class="hero-art">${bowl()}</div></section><section aria-labelledby="inventory-title"><div class="section-heading"><h2 id="inventory-title">What's in your fridge</h2><small>Added by you, kept simple.</small></div><div class="inventory-panel">${inputForm('inventory','Add an ingredient','e.g. carrots, chickpeas, yogurt')}${state.inventory.length?`<div class="inventory-head" aria-hidden="true"><span>INGREDIENT</span><span>DATE ADDED</span><span></span></div>${state.inventory.map(item=>`<div class="inventory-row"><span class="ingredient"><span class="ingredient-icon" aria-hidden="true">${icons(item.name)}</span>${escapeHTML(item.name)}</span><span class="added-date"><time datetime="${item.addedAt}">${date(item.addedAt)}</time></span><button class="icon-button delete-button" data-action="delete-inventory" data-id="${item.id}" aria-label="Remove ${escapeHTML(item.name)} from fridge">×</button></div>`).join('')}`:empty('Start with one ingredient.','Add something you have at home, then explore what you could make.','','❧')}</div><p class="under-note">Dates show when you added each ingredient. Update your fridge manually as things change.</p></section><div class="bottom-cards"><article class="mini-card"><p class="eyebrow">MAKE IT YOURS</p><h3>A kitchen that knows your preferences.</h3><p>Choose dietary preferences and declare allergens for recipe requests.</p><a href="#preferences">Set your preferences <span aria-hidden="true">↗</span></a></article><article class="mini-card"><p class="eyebrow">THE NEXT GROCERY RUN</p><h3>Only the things you're missing.</h3><p>Add missing recipe ingredients to your shopping list in one go.</p><a href="#shopping">Open shopping list <span aria-hidden="true">↗</span></a></article></div>`;
}
function recipeCard(recipe,remove=false) { return `<article class="recipe-card"><div class="recipe-art">${bowl()}</div><div class="recipe-card-content"><p class="section-kicker">FROM YOUR EVERYDAY INGREDIENTS</p><h3>${escapeHTML(recipe.title)}</h3><div class="recipe-meta"><span>◷ ${recipe.cookingMinutes} min · est.</span><span>${recipe.caloriesPerServing} kcal / serving · est.</span></div><p>${escapeHTML(recipe.description)}</p><div class="recipe-actions"><button class="btn btn-primary" data-action="open-recipe" data-id="${recipe.id}">View recipe <span aria-hidden="true">↗</span></button><button class="btn btn-secondary" data-action="${remove?'remove-favorite':'favorite'}" data-id="${recipe.id}" ${remove?'':`aria-pressed="${state.favorites.has(recipe.id)}"`}>${remove?'Remove':state.favorites.has(recipe.id)?'♥ Saved':'♡ Save'}</button></div></div></article>`; }
function recipesPage() {
  const tags=[...state.preferences.dietary,...state.preferences.allergens.map(x=>`Exclude ${x.toLowerCase()}`)];
  let content='';
  if(state.generation==='loading') content=`<div class="panel" aria-busy="true">${empty('A few good ideas are on their way.','Finding something to make with your ingredients.','<span class="spinner" aria-hidden="true"></span><p class="loading-label" role="status">Generating recipe suggestions…</p>')}</div>`;
  else if(state.generation==='error') content=`<div class="notice error" role="alert"><strong>We couldn't get recipes this time.</strong>Your fridge, preferences and saved lists are unchanged. Try again when you're ready.</div><button class="btn btn-primary" data-action="retry">Try again</button>`+(state.recipes.length?`<div class="section-heading" style="margin-top:28px"><h2>Your previous suggestions</h2></div><div class="recipes-grid">${state.recipes.map(r=>recipeCard(r)).join('')}</div>`:'');
  else if(state.generation==='empty') content=`<div class="panel">${empty('A little something to start with.','Add at least one ingredient to your fridge before asking for recipes.','<a class="btn btn-primary" href="#fridge">Add an ingredient</a>')}</div>`;
  else if(state.recipes.length) content=`<div class="recipes-grid">${state.recipes.map(r=>recipeCard(r)).join('')}</div>`;
  else content=`<div class="panel">${empty('What could you make today?','Get a few recipe ideas using your fridge and your saved preferences.','<button class="btn btn-primary" data-action="generate">Find recipes</button>','❧')}</div>`;
  return heading('A LITTLE INSPIRATION','Make something good.','Recipe ideas that start with your ingredients.')+`<div class="toolbar">${tags.map(t=>`<span class="tag">${escapeHTML(t)}</span>`).join('')}<a class="tag" href="#preferences">Edit preferences ↗</a><button class="btn btn-secondary" data-action="generate" ${state.generation==='loading'?'disabled':''}>Find new recipes</button></div><div class="notice">Cooking times and calories are AI estimates. Review every ingredient, especially if you have allergies; suggestions cannot verify hidden ingredients or cross-contamination.</div>${content}`;
}
function shopping() { return heading('ONE LESS THING TO REMEMBER','Your next grocery run.','Keep a simple list of the things you want to pick up.',`${state.shopping.length} items on your list`)+`<div class="panel">${inputForm('shopping','Add a shopping item','e.g. onion or lemon')}${state.shopping.length?state.shopping.map(item=>`<div class="inventory-row"><span class="ingredient"><span class="ingredient-icon" aria-hidden="true">${icons(item.name)}</span>${escapeHTML(item.name)}</span><span></span><button class="icon-button delete-button" data-action="delete-shopping" data-id="${item.id}" aria-label="Remove ${escapeHTML(item.name)} from shopping list">×</button></div>`).join(''):empty('Nothing on the list just yet.','Add an item above, or add the missing ingredients from a recipe.','<a class="btn btn-secondary" href="#recipes">Explore recipes</a>','◐')}</div><p class="under-note">Removing an item from this list doesn't add it to your fridge. Add ingredients to your fridge manually.</p>`; }
function saved() {
  const favorites=recipeFixtures.filter(recipe=>state.favorites.has(recipe.id));
  const history=[...state.history.values()].sort((a,b)=>b.lastViewedAt.localeCompare(a.lastViewedAt)||a.recipe.id.localeCompare(b.recipe.id));
  const content=state.savedTab==='favorites'?(favorites.length?`<div class="recipes-grid">${favorites.map(r=>recipeCard(r,true)).join('')}</div>`:`<div class="panel">${empty('Keep the good ones close.','Save a recipe you like and it will be waiting here.','<a class="btn btn-primary" href="#recipes">Find a recipe to save</a>','♡')}</div>`):(history.length?`<div class="panel">${history.map(({recipe,lastViewedAt})=>`<article class="history-row"><div><h3>${escapeHTML(recipe.title)}</h3><p>Last viewed <time datetime="${lastViewedAt}">${new Date(lastViewedAt).toLocaleString('en-GB',{day:'numeric',month:'short',hour:'2-digit',minute:'2-digit'})}</time></p></div><button class="btn btn-secondary" data-action="open-recipe" data-id="${recipe.id}">Open recipe ↗</button></article>`).join('')}</div>`:`<div class="panel">${empty('A place for your recent finds.','Recipes appear here after you open their details.','<a class="btn btn-primary" href="#recipes">Explore recipes</a>','◷')}</div>`);
  return heading('WORTH COMING BACK TO','Your recipe collection.','Favorites for another day. Recent recipes for a second look.')+`<div class="tabs" role="group" aria-label="Recipe collection view"><button data-action="saved-tab" data-tab="favorites" aria-pressed="${state.savedTab==='favorites'}">Favorites (${favorites.length})</button><button data-action="saved-tab" data-tab="history" aria-pressed="${state.savedTab==='history'}">Recently viewed (${history.length})</button></div>${content}`;
}
function preferences() {
  const options=(name,values)=>values.map(value=>`<label class="choice"><input type="checkbox" name="${name}" value="${value}" ${state.preferences[name].includes(value)?'checked':''}>${value}</label>`).join('');
  return heading('A KITCHEN THAT FEELS LIKE YOU','Your preferences.','These choices accompany your next recipe request.')+`<div class="preference-layout"><form id="preferences-form" class="panel preference-panel"><fieldset><legend>How do you like to eat?</legend><p>Choose any that apply, or leave them all unchecked.</p><div class="choices">${options('dietary',['Vegetarian','Vegan','Gluten-free','Lactose-free'])}</div></fieldset><fieldset><legend>Allergens to exclude</legend><p>Declare ingredients you want recipe suggestions to avoid.</p><div class="choices">${options('allergens',['Peanut','Milk','Egg','Wheat','Soy','Sesame'])}</div></fieldset><button class="btn btn-primary" type="submit">Save preferences <span aria-hidden="true">↗</span></button><button class="btn text-button" type="button" data-action="clear-preferences">Clear selections</button></form><aside class="preference-note"><p class="section-kicker">A THOUGHTFUL START</p><h3>Preferences help.<br>Your own review matters.</h3><p>Recipe suggestions are generated by AI. Always review the full ingredient list and your own dietary needs.</p><p>Hidden ingredients and cross-contamination cannot be verified by Fridgely.</p></aside></div>`;
}
function auth() { const register=state.route==='register';return `<div class="auth-wrap"><div class="auth-copy"><p class="section-kicker">LESS WASTE. MORE POSSIBILITY.</p><h1>Good meals.<br>From what you have.</h1><p>A personal little space for your ingredients, recipes and everyday inspiration.</p><div class="hero-art">${bowl()}</div></div><form id="auth-form" class="auth-panel" novalidate><h2>${register?'Make yourself at home.':'Welcome back.'}</h2><p>${register?'Create your account and start your kitchen.':'Sign in to return to your kitchen.'}</p>${state.expired?'<div class="session-note" role="status">Your session has expired. Sign in again to continue.</div>':''}<div class="field"><label for="auth-email">Email address</label><input id="auth-email" name="email" type="email" autocomplete="email" placeholder="you@example.com" aria-describedby="auth-error"></div><div class="field"><label for="auth-password">Password</label><input id="auth-password" name="password" type="password" minlength="8" autocomplete="${register?'new-password':'current-password'}" placeholder="${register?'At least 8 characters':'Your password'}" aria-describedby="auth-error"></div><p id="auth-error" class="field-error hide" role="alert"></p><button class="btn btn-primary" type="submit">${register?'Create account':'Sign in'} <span aria-hidden="true">↗</span></button><div class="auth-switch">${register?'Already have an account? <a href="#signin">Sign in</a>':'New around here? <a href="#register">Create account</a>'}</div></form></div>`; }
function render() {
  const routes=[['fridge','▤','My fridge'],['recipes','✳','Recipes'],['shopping','♧','Shopping list'],['saved','♡','Saved recipes'],['preferences','☷','Preferences']];
  $('#navigation').innerHTML=routes.map(([route,icon,title])=>`<a href="#${route}" ${state.route===route?'aria-current="page"':''}><span class="nav-icon" aria-hidden="true">${icon}</span>${title}${route==='fridge'?`<span class="nav-count">${state.inventory.length}</span>`:''}</a>`).join('');
  $('#signout').classList.toggle('hide',!state.signedIn);
  $('#main').innerHTML=state.signedIn?({fridge:inventory,recipes:recipesPage,shopping,saved,preferences}[state.route]||inventory)():auth();
  document.title=`Fridgely · ${state.signedIn?routes.find(r=>r[0]===state.route)?.[2]||'My fridge':state.route==='register'?'Create account':'Sign in'}`;
}
function navigate(route) {
  const allowed=['fridge','recipes','shopping','saved','preferences','signin','register'];
  state.route=allowed.includes(route)?route:'fridge';
  if(!state.signedIn&&!['signin','register'].includes(state.route))state.route='signin';
  if(state.signedIn&&['signin','register'].includes(state.route)) {state.signedIn=false;}
  render();
}
function generate() {
  clearTimeout(generationTimer);state.route='recipes';location.hash='recipes';
  if(!state.inventory.length){state.generation='empty';render();return;}
  state.generation='loading';render();
  generationTimer=setTimeout(()=>{state.generation=state.forceError?'error':'ready';if(!state.forceError)state.recipes=structuredClone(recipeFixtures);render();},700);
}
function openRecipe(id) {
  const recipe=state.recipes.find(r=>r.id===id)||recipeFixtures.find(r=>r.id===id);
  if(!recipe)return;
  modalRecipeId=id;
  state.history.set(id,{recipe,lastViewedAt:clock()});
  const have=new Set(state.inventory.map(item=>normalize(item.name)));
  $('#recipe-dialog').innerHTML=`<div class="dialog-top"><span>FROM YOUR KITCHEN</span><button class="icon-button" data-action="close-dialog" aria-label="Close recipe details">×</button></div><div class="dialog-content"><p class="section-kicker">SOMETHING GOOD TO MAKE</p><h2 id="recipe-title">${escapeHTML(recipe.title)}</h2><div class="recipe-meta"><span>${recipe.cookingMinutes} min · estimated</span><span>${recipe.caloriesPerServing} kcal / serving · estimated</span><span>Serves ${recipe.servings}</span></div><div class="notice">AI-generated estimates. Review all ingredients and your dietary needs before cooking.</div><div class="detail-columns"><section><h3>Ingredients</h3><ul>${recipe.ingredients.map(name=>`<li>${escapeHTML(name)}${have.has(normalize(name))?' <span class="available">· in your fridge</span>':' · missing'}</li>`).join('')}</ul></section><section><h3>Let's make it</h3><ol>${recipe.steps.map(step=>`<li>${escapeHTML(step)}</li>`).join('')}</ol></section></div><div class="dialog-actions"><button class="btn btn-primary" data-action="add-missing" data-id="${recipe.id}">Add missing ingredients ↗</button><button class="btn btn-secondary" data-action="favorite" data-id="${recipe.id}" aria-pressed="${state.favorites.has(id)}">${state.favorites.has(id)?'♥ Saved':'♡ Save recipe'}</button></div><p class="under-note">Your fridge stays as it is. Remove ingredients manually when you need to.</p></div>`;
  if(!$('#recipe-dialog').open)$('#recipe-dialog').showModal();
  render();
}
$('#recipe-dialog').addEventListener('close',()=>{
  const target=[...document.querySelectorAll('#main [data-action="open-recipe"]')].find(button=>button.dataset.id===modalRecipeId)||$('#main');
  target.focus();
});
function error(id,message,inputSelector) { const el=$(`#${id}-error`);el.textContent=message;el.classList.remove('hide');const input=inputSelector?$(inputSelector):$(`#${id}-name`)||$('#auth-email');input.setAttribute('aria-invalid','true');input.focus(); }
document.addEventListener('submit',event=>{
  event.preventDefault();const form=event.target;
  if(form.id==='auth-form') {
    const email=form.elements.email.value.trim(),password=form.elements.password.value;
    if(!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)){error('auth','Enter a valid email address.','#auth-email');return;}
    if(password.length<8){error('auth','Enter a password of at least eight characters.','#auth-password');return;}
    // Concept navigation only. Never persist or send credentials.
    state.signedIn=true;state.expired=false;state.route='fridge';form.reset();location.hash='fridge';render();announce('Welcome to your kitchen.');return;
  }
  if(!state.signedIn)return;
  if(['inventory-form','shopping-form'].includes(form.id)) {
    const kind=form.id.split('-')[0],name=form.elements.name.value.trim();
    if(!name){error(kind,'Enter an ingredient name before adding it.');return;}
    if(kind==='shopping'&&state.shopping.some(item=>normalize(item.name)===normalize(name))){announce('That item is already on your list.');return;}
    state[kind].push({id:`local-${state.nextId++}`,name,...(kind==='inventory'?{addedAt:clock()}:{})});render();$(`#${kind}-name`).focus();announce(`${name} added.`);
  } else if(form.id==='preferences-form') {
    const data=new FormData(form);state.preferences={dietary:data.getAll('dietary'),allergens:data.getAll('allergens')};render();announce('Preferences saved for your next recipe request.');
  }
});
document.addEventListener('click',event=>{
  const button=event.target.closest('[data-action]');if(!button)return;
  const {action,id,tab}=button.dataset;
  if(action==='close-dialog'){$('#recipe-dialog').close();return;}
  if(!state.signedIn)return;
  if(action==='generate')generate();
  else if(action==='retry'){state.forceError=false;$('#preview-state').value='normal';generate();}
  else if(action==='open-recipe')openRecipe(id);
  else if(action==='delete-inventory'||action==='delete-shopping') {
    const kind=action==='delete-inventory'?'inventory':'shopping';state[kind]=state[kind].filter(item=>item.id!==id);render();announce(kind==='inventory'?'Ingredient removed from fridge.':'Item removed from shopping list.');
  } else if(action==='favorite') {
    state.favorites.add(id);button.textContent='♥ Saved';button.setAttribute('aria-pressed','true');render();announce('Recipe saved to favorites.');
  } else if(action==='remove-favorite') {state.favorites.delete(id);render();announce('Favorite removed. Your viewed history is unchanged.');}
  else if(action==='saved-tab'){state.savedTab=tab;render();}
  else if(action==='clear-preferences'){document.querySelectorAll('#preferences-form input').forEach(input=>input.checked=false);announce('Selections cleared. Save preferences to apply.');}
  else if(action==='add-missing') {
    const recipe=recipeFixtures.find(recipe=>recipe.id===id);const have=new Set(state.inventory.map(item=>normalize(item.name))),inList=new Set(state.shopping.map(item=>normalize(item.name)));let added=0;
    for(const name of recipe.ingredients){const key=normalize(name);if(!have.has(key)&&!inList.has(key)){state.shopping.push({id:`local-${state.nextId++}`,name});inList.add(key);added++;}}
    render();announce(added?`${added} missing ingredient${added>1?'s':''} added to shopping.`:'Missing ingredients are already on your list.');
  }
});
$('#signout').addEventListener('click',()=>{clearTimeout(generationTimer);$('#recipe-dialog').close();state.signedIn=false;state.route='signin';location.hash='signin';render();});
$('#preview-state').addEventListener('change',event=>{
  clearTimeout(generationTimer);$('#recipe-dialog').close();const value=event.target.value;
  if(value==='normal')seed();
  else if(value==='empty'){seed();state.inventory=[];}
  else if(value==='expired'){state.signedIn=false;state.expired=true;state.route='signin';}
  else {state.signedIn=true;state.route='recipes';state.generation=value==='loading'?'loading':'error';state.forceError=value==='error';}
  location.hash=state.route;render();
});
$('#reset-preview').addEventListener('click',()=>{$('#recipe-dialog').close();seed();$('#preview-state').value='normal';location.hash='fridge';render();announce('Preview reset to sample data.');});
window.addEventListener('hashchange',()=>navigate(location.hash.slice(1)));
seed();navigate(location.hash.slice(1)||'fridge');
