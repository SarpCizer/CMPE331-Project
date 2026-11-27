import { useEffect, useState } from "react";
import { useOutletContext } from "react-router-dom";
import ChangePassword from "../components/ChangePassword";
import FieldError from "../components/FieldError";
import { formatPreferences } from "../preferences";
import { focusInvalid, preferenceField } from "../utils/forms";

const help = "mx-0 mt-2 mb-6 block";

function Preferences({ value, run, api }) {
  const [dietary, setDietary] = useState(formatPreferences(value.dietary)),
    [allergens, setAllergens] = useState(formatPreferences(value.allergens)),
    [errors, setErrors] = useState({});
  useEffect(() => {
    setDietary(formatPreferences(value.dietary));
    setAllergens(formatPreferences(value.allergens));
  }, [value]);
  function submit(event) {
    event.preventDefault();
    const fields = {
      dietary: preferenceField(dietary),
      allergens: preferenceField(allergens),
    };
    const invalid = Object.fromEntries(
      Object.entries(fields)
        .map(([key, field]) => [key, field.error])
        .filter(([, message]) => message),
    );
    setErrors(invalid);
    if (Object.keys(invalid).length) {
      focusInvalid(event.currentTarget, invalid);
      return;
    }
    const body = {
      dietary: fields.dietary.values,
      allergens: fields.allergens.values,
    };
    run(
      () => api("/profile/preferences", { method: "PUT", body }),
      "Preferences saved.",
      ["preferences"],
    );
  }
  return (
    <section className="panel max-w-[750px]">
      <span className="eyebrow">MAKE IT YOURS</span>
      <h2 className="mobile:text-[1.6rem]">A kitchen that knows you.</h2>
      <p className="max-w-[570px] text-[0.95rem]">
        Your saved preferences are included whenever you ask for recipes.
      </p>
      <form className="mt-[30px]" noValidate onSubmit={submit}>
        <label htmlFor="dietary">Dietary preferences</label>
        <textarea
          id="dietary"
          rows="2"
          value={dietary}
          onChange={(e) => {
            setDietary(e.target.value);
            setErrors((value) => ({ ...value, dietary: "" }));
          }}
          placeholder="Vegetarian, vegan…"
          aria-invalid={!!errors.dietary}
          aria-describedby={`dietary-help${errors.dietary ? " dietary-error" : ""}`}
        />
        <small id="dietary-help" className={help}>
          Separate preferences with commas. Quote a name containing commas; use
          two double quotes for a quote inside a name.
        </small>
        <FieldError id="dietary-error">{errors.dietary}</FieldError>
        <label htmlFor="allergens">Ingredients to exclude</label>
        <textarea
          id="allergens"
          rows="2"
          value={allergens}
          onChange={(e) => {
            setAllergens(e.target.value);
            setErrors((value) => ({ ...value, allergens: "" }));
          }}
          placeholder="Peanut, sesame…"
          aria-invalid={!!errors.allergens}
          aria-describedby={`allergens-help${errors.allergens ? " allergens-error" : ""}`}
        />
        <small id="allergens-help" className={help}>
          Separate names with commas. Quote a name containing commas; use two
          double quotes for a quote inside a name. Review recipe ingredients
          before cooking.
        </small>
        <FieldError id="allergens-error">{errors.allergens}</FieldError>
        <button type="submit" className="btn-primary mb-4">
          Save preferences
        </button>
        <p className="muted mb-0">
          Clear either field and save to remove its saved entries.
        </p>
      </form>
    </section>
  );
}

export default function PreferencesPage() {
  const { data, api, run, clearSession } = useOutletContext();
  return <>
    <Preferences value={data.preferences} api={api} run={run} />
    <ChangePassword api={api} run={run} clearSession={clearSession} />
  </>;
}
