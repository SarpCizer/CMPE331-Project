import { useState } from 'react';
import { cookingQuantity } from '../utils/cooking';

function savedConfirmation(key) {
  try {
    const saved = JSON.parse(sessionStorage.getItem(key));
    return saved && typeof saved.requestId === 'string' && Array.isArray(saved.items) && saved.items.length ? saved : null;
  } catch { return null; }
}

export default function CookRecipe({ recipe, inventory, run, api, busy, refreshInventory, onCancel, onComplete }) {
  const storageKey = `fridgely.cooking.${recipe.id}`;
  const [pending, setPending] = useState(() => savedConfirmation(storageKey));
  const [rows, setRows] = useState(() => recipe.ingredients.map((name, index) => {
    const matches = inventory.filter(item => item.name.trim().toLowerCase() === name.trim().toLowerCase());
    const item = matches.find(item => item.quantity > 0) || matches[0];
    return { name, measurement: recipe.ingredientAmounts?.[index], matches,
      id: item?.id || '', amount: item ? cookingQuantity(recipe.ingredientAmounts?.[index], item.unit) : '' };
  }));
  const [validation, setValidation] = useState('');
  function change(index, changes) {
    setRows(value => value.map((row, i) => i === index ? { ...row, ...changes } : row));
    setValidation('');
  }
  async function confirm(event) {
    event.preventDefault();
    // Reconcile the original operation before checking refreshed stock. It may
    // already have depleted an entry; rebuilding its body would create a new action.
    if (pending) { await submit(pending); return; }
    const items = [];
    for (const row of rows) {
      const item = inventory.find(item => item.id === row.id);
      if (!item || item.quantity == null || item.quantity === 0) continue;
      const quantity = Number(row.amount);
      if (row.amount.trim() === '' || !Number.isFinite(quantity) || quantity < 0 || quantity > item.quantity ||
          (['pcs', 'pack', 'bunch'].includes(item.unit) && !Number.isInteger(quantity))) {
        setValidation('Review each amount: enter a valid quantity within your stock, or 0 to skip.');
        return;
      }
      if (quantity > 0) items.push({ inventoryId: item.id, quantity, unit: item.unit });
    }
    if (!items.length) { setValidation('Choose at least one stocked ingredient to deduct.'); return; }
    const body = { requestId: crypto.randomUUID(), items };
    try { sessionStorage.setItem(storageKey, JSON.stringify(body)); }
    catch { setValidation('This browser could not save the confirmation safely. No request was sent.'); return; }
    setPending(body);
    await submit(body);
  }
  async function submit(body) {
    const result = await run(async () => {
      try {
        return await api(`/recipes/${recipe.id}/cook`, { method: 'POST', body });
      } catch (error) {
        // These definitive rejections leave the submitted transaction unchanged.
        // A network/5xx/expired-session result is uncertain, so preserve its body.
        if ([400, 404, 409].includes(error.status)) {
          sessionStorage.removeItem(storageKey);
          setPending(null);
        }
        if (error.status === 409) {
          await refreshInventory();
          throw new Error('Stock changed or is insufficient. Review the quantities and try again.');
        }
        throw error;
      }
    }, 'Recipe cooked. Fridge quantities updated.', ['inventory']);
    if (result) { sessionStorage.removeItem(storageKey); setPending(null); onComplete(); }
  }
  return <form noValidate onSubmit={confirm} className="my-5 rounded-xl border border-line p-4">
    <h3>{pending ? 'Check previous cooking confirmation' : 'Confirm ingredients used'}</h3>
    {pending ? <>
      <p>Your previous confirmation may already have been saved. Retry it to check the result before starting another cooking.</p>
      <ul>{pending.items.map(item => <li key={item.inventoryId}>
        {inventory.find(stock => stock.id === item.inventoryId)?.name || 'Saved ingredient'} · {item.quantity} {item.unit}
      </li>)}</ul>
    </> : <>
    <p>Amounts below are for the full recipe ({recipe.servings} servings). Review what you actually used. Enter 0 to skip an ingredient. Only listed fridge stock is deducted.</p>
    {rows.map((row, index) => {
      const item = inventory.find(item => item.id === row.id);
      return <div key={index} className="my-4">
        <strong>{row.name}{row.measurement ? ` · Recipe: ${row.measurement}` : ''}</strong>
        {row.matches.length > 1 && <><label htmlFor={`stock-${index}`}>Fridge entry for {row.name}</label>
          <select id={`stock-${index}`} disabled={busy} value={row.id} onChange={event => {
            const selected = inventory.find(item => item.id === event.target.value);
            change(index, { id: selected.id, amount: cookingQuantity(row.measurement, selected.unit) });
          }}>{row.matches.map(item => <option key={item.id} value={item.id}>{item.name} · {item.quantity ?? 'Unknown'} {item.unit}</option>)}</select></>}
        {!item || item.quantity === 0 ? <p>Not in stock — no deduction.</p> : item.quantity == null ?
          <p>Stock amount unknown. Set its quantity in My Fridge before deducting.</p> : <>
            <label htmlFor={`used-${index}`}>Used {row.name} ({item.unit})</label>
            <input id={`used-${index}`} disabled={busy} type="number" min="0" max={item.quantity} step={['pcs','pack','bunch'].includes(item.unit) ? '1' : 'any'}
              value={row.amount} onChange={event => change(index, { amount: event.target.value })} />
            <p className="text-sm">Available: {item.quantity} {item.unit}{row.amount !== '' && Number(row.amount) <= item.quantity && Number(row.amount) >= 0 ? ` · Remaining: ${Number((item.quantity - Number(row.amount)).toPrecision(12))} ${item.unit}` : ''}</p>
          </>}
      </div>;
    })}</>}
    {validation && <p className="alert-error" role="alert">{validation}</p>}
    <div className="flex flex-wrap gap-3">
      <button className="btn-primary" disabled={busy} type="submit">{pending ? 'Retry previous confirmation' : 'Confirm cooking and update fridge'}</button>
      <button className="btn-secondary" disabled={busy} type="button" onClick={onCancel}>{pending ? 'Close confirmation' : 'Cancel cooking'}</button>
    </div>
  </form>;
}
