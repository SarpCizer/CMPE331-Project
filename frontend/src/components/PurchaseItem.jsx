import { useState } from 'react';
import ShoppingAmount, { amountInput } from './ShoppingAmount';

export default function PurchaseItem({ item, api, run, busy, refresh, onCancel }) {
  const [quantity, setQuantity] = useState(String(item.quantity ?? ''));
  const [unit, setUnit] = useState(item.unit ?? 'pcs');
  const [error, setError] = useState('');
  return <form noValidate className="my-3 w-full rounded-xl border border-line p-4" onSubmit={async event => {
    event.preventDefault();
    const amount = amountInput(quantity, unit, true);
    setError(amount.error);
    if (amount.error) { event.currentTarget.querySelector('input').focus(); return; }
    await run(async () => {
      try {
        return await api(`/shopping-items/${item.id}/purchase`, { method: 'POST', body: amount.body });
      } catch (failure) {
        if ([404, 409].includes(failure.status)) await refresh();
        throw failure;
      }
    }, 'Purchase recorded. Your fridge has been updated.', ['shopping', 'inventory']);
  }}>
    <h3>Confirm purchase: {item.name}</h3>
    <p className="text-sm">Review what you actually bought. This amount is added to your fridge and the item leaves this list. Compatible units are converted; unknown or incompatible stock stays separate.</p>
    <div className="flex flex-wrap items-end gap-3">
      <ShoppingAmount id={`purchase-${item.id}`} quantity={quantity} unit={unit}
        setQuantity={value => { setQuantity(value); setError(''); }} setUnit={value => { setUnit(value); setError(''); }}
        error={error} disabled={busy} required legacyUnit={item.unit} />
      <button disabled={busy} className="btn-primary mobile:w-full" type="submit">Confirm purchase and add to fridge</button>
      <button disabled={busy} className="btn-secondary mobile:w-full" type="button" onClick={onCancel}>Cancel purchase</button>
    </div>
  </form>;
}
