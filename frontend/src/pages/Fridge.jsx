import { useState } from "react";
import { Link, useOutletContext } from "react-router-dom";
import Empty from "../components/Empty";
import FieldError from "../components/FieldError";
import Icon from "../components/Icon";
import ProduceArt from "../components/ProduceArt";
import { nameError } from "../utils/forms";
import {
  countBadge,
  inlineForm,
  inlineSubmit,
  itemList,
  itemRow,
  itemSymbol,
  removeButton,
  sectionHeading,
  sectionTitle,
} from "../components/listStyles";

const statCard =
  "flex items-center gap-[13px] rounded-[15px] border border-line bg-white px-[22px] py-[19px] text-[0.8rem] text-[#6b7a6d] mobile:gap-[10px] mobile:px-[13px] mobile:py-4 mobile:text-[0.7rem]";
const statIcon = "shrink-0 text-[#56765a] mobile:hidden";

function Fridge({ items, run, api }) {
  const [name, setName] = useState(""),
    [quantity, setQuantity] = useState("1"),
    [unit, setUnit] = useState("pcs"),
    [editing, setEditing] = useState(null),
    [search, setSearch] = useState(""),
    [error, setError] = useState("");
  async function add(event) {
    event.preventDefault();
    const amount = Number(quantity);
    const invalid = (editing ? "" : nameError(name, "an ingredient")) ||
      (!Number.isFinite(amount) || amount <= 0 || amount > 1000000 ||
       (["pcs","pack","bunch"].includes(unit) && !Number.isInteger(amount))
        ? "Enter a valid positive quantity (whole numbers for count units)." : "");
    setError(invalid);
    if (invalid) {
      event.currentTarget.querySelector("input").focus();
      return;
    }
    if (
      await run(
        () => editing
          ? api(`/inventory/${editing}`, { method: "PATCH", body: { quantity: amount, unit } })
          : api("/inventory", { method: "POST", body: { name, quantity: amount, unit } }),
        editing ? "Ingredient updated." : "Ingredient added.",
        ["inventory"],
      )
    )
      resetForm();
  }
  function resetForm() {
    setName(""); setQuantity("1"); setUnit("pcs"); setEditing(null); setError("");
  }
  const visible = items.filter((item) =>
    item.name.toLocaleLowerCase().includes(search.toLocaleLowerCase()),
  );
  return (
    <>
      <section className="flex items-center justify-between gap-5 overflow-hidden rounded-[24px] bg-[#e4eee3] px-9 py-8 tablet:p-7 mobile:relative mobile:p-[25px]">
        <div className="mobile:relative mobile:z-[1]">
          <span className="eyebrow text-[0.65rem]">
            A KITCHEN FULL OF POSSIBILITIES
          </span>
          <h2 className="mb-4 font-serif text-[2.65rem] font-normal tracking-[-0.045em] tablet:text-[2.25rem] mobile:text-[2.1rem]">
            Use what you have.
            <br />
            <em className="font-normal text-[#497353]">Love what you make.</em>
          </h2>
          <p className="mb-5 max-w-[370px] text-[0.9rem] mobile:max-w-[230px]">
            Your next good meal might already be in the fridge.
          </p>
          <Link
            className="btn-primary px-[17px] py-[10px] text-[0.8rem]"
            to="/recipes"
          >
            Find a recipe
          </Link>
        </div>
        <ProduceArt className="w-[210px] tablet:w-[155px] mobile:absolute mobile:-right-5 mobile:bottom-[5px] mobile:w-[140px] mobile:opacity-45" />
      </section>
      <div className="grid grid-cols-2 gap-5 py-[25px] mobile:gap-[10px] mobile:py-[18px]">
        <div className={statCard}>
          <Icon name="fridge" className={statIcon} />
          <strong className="text-[1.8rem] leading-[1.2] font-semibold text-ink mobile:text-[1.6rem]">
            {items.length}
          </strong>
          <span>
            {items.length === 1 ? "ingredient" : "ingredients"} in your fridge
          </span>
        </div>
        <div className={statCard}>
          <Icon name="leaf" className={statIcon} />
          <span>
            Less forgotten food.
            <br />
            <strong className="text-[0.85rem] leading-[1.2] font-[550] text-ink mobile:text-[0.75rem]">
              More everyday possibilities.
            </strong>
          </span>
        </div>
      </div>
      <section className="panel">
        <div className={sectionHeading}>
          <div>
            <h2 className={sectionTitle}>Your ingredients</h2>
            <p className="mb-0 text-[0.85rem]">
              A small list with a lot of potential.
            </p>
          </div>
          <span className={countBadge}>
            {items.length} {items.length === 1 ? "item" : "items"}
          </span>
        </div>
        <form className={inlineForm} noValidate onSubmit={add}>
          <div className="min-w-0 flex-1 mobile:basis-full">
            <label htmlFor="ingredient" className="text-[0.8rem]">
              Add an ingredient
            </label>
            <input
              id="ingredient"
              value={name}
              disabled={!!editing}
              onChange={(e) => {
                setName(e.target.value);
                setError("");
              }}
              required
              maxLength="256"
              placeholder="Tomatoes, rice, a little inspiration…"
              className="text-[0.9rem]"
              aria-invalid={!!error}
              aria-describedby={error ? "ingredient-error" : undefined}
            />
            <FieldError id="ingredient-error">{error}</FieldError>
          </div>
          <div className="w-[100px] mobile:flex-1">
            <label htmlFor="quantity" className="text-[0.8rem]">Quantity</label>
            <input id="quantity" type="number" min="0.000001" max="1000000" step="any"
              value={quantity} onChange={(e) => setQuantity(e.target.value)} required />
          </div>
          <div className="w-[110px] mobile:flex-1">
            <label htmlFor="unit" className="text-[0.8rem]">Unit</label>
            <select id="unit" value={unit} onChange={(e) => setUnit(e.target.value)}
              className="w-full rounded-lg border border-line bg-white p-2">
              {["pcs","kg","g","L","ml","pack","bunch"].map((value) =>
                <option key={value} value={value}>{value}</option>)}
            </select>
          </div>
          {editing && <button type="button" onClick={resetForm}>Cancel edit</button>}
          <button type="submit" className={inlineSubmit}>
            <Icon name="plus" className="w-[18px]" />
            {editing ? "Save quantity" : "Add ingredient"}
          </button>
        </form>
        {items.length > 0 && (
          <div className="mt-[22px] max-w-[300px] mobile:max-w-none">
            <label htmlFor="search" className="text-[0.8rem]">
              Search your fridge
            </label>
            <input
              id="search"
              type="search"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Find an ingredient"
              className="px-3 py-[10px] text-[0.9rem]"
            />
          </div>
        )}
        {!visible.length ? (
          <Empty
            icon="fridge"
            title={items.length ? "No matching ingredients" : "A fresh canvas"}
          >
            {items.length
              ? "Try a different search."
              : "Add your first ingredient to start finding meals."}
          </Empty>
        ) : (
          <ul className={itemList}>
            {visible.map((item) => (
              <li key={item.id} className={itemRow}>
                <span className={itemSymbol}>
                  <Icon name="leaf" />
                </span>
                <div className="min-w-0 flex-1">
                  <strong className="block text-[0.95rem] font-[550] wrap-anywhere">
                    {item.name}
                    {item.quantity != null && <span className="ml-2 text-[#607565]">· {item.quantity} {item.unit}</span>}
                  </strong>
                  <span className="block text-[0.8rem] text-[#607565]">
                    Added{" "}
                    {new Intl.DateTimeFormat("en", {
                      dateStyle: "medium",
                    }).format(new Date(item.addedAt))}
                  </span>
                </div>
                <button type="button" className={removeButton} aria-label={`Edit quantity for ${item.name}`}
                  onClick={() => {
                    setEditing(item.id); setName(item.name);
                    setQuantity(String(item.quantity ?? 1)); setUnit(item.unit ?? "pcs"); setError("");
                    document.getElementById("quantity")?.focus();
                  }}>Edit</button>
                <button
                  className={removeButton}
                  aria-label={`Remove ${item.name}`}
                  onClick={() =>
                    run(
                      () => api(`/inventory/${item.id}`, { method: "DELETE" }),
                      "Ingredient removed.",
                      ["inventory"],
                    )
                  }
                >
                  Remove
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>
    </>
  );
}

export default function FridgePage() {
  const { data, api, run } = useOutletContext();
  return <Fridge items={data.inventory} api={api} run={run} />;
}
