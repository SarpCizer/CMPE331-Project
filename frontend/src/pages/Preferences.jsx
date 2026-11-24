import { useEffect, useState } from "react";
import { useOutletContext } from "react-router-dom";
import FieldError from "../components/FieldError";
import { focusInvalid, preferenceError, splitPreferences } from "../utils/forms";

function Preferences({ value, run, api }) {
  const [dietary, setDietary] = useState(value.dietary.join(", ")),
    [allergens, setAllergens] = useState(value.allergens.join(", ")),
    [errors, setErrors] = useState({});
  useEffect(() => {
    setDietary(value.dietary.join(", "));
    setAllergens(value.allergens.join(", "));
  }, [value]);
  function submit(event) {
    event.preventDefault();
    const body = {
      dietary: splitPreferences(dietary),
      allergens: splitPreferences(allergens),
    };
    const invalid = Object.fromEntries(
      Object.entries(body)
        .map(([key, values]) => [key, preferenceError(values)])
        .filter(([, message]) => message),
    );
    setErrors(invalid);
    if (Object.keys(invalid).length) {
      focusInvalid(event.currentTarget, invalid);
      return;
    }
    run(
      () => api("/profile/preferences", { method: "PUT", body }),
      "Preferences saved.",
      ["preferences"],
    );
  }
  return (
    <section className="panel preferences">
      <span className="eyebrow">MAKE IT YOURS</span>
      <h2>A kitchen that knows you.</h2>
      <p>Your saved preferences are included whenever you ask for recipes.</p>
      <form noValidate onSubmit={submit}>
        <label htmlFor="dietary">Dietary preferences</label>
        <input
          id="dietary"
          value={dietary}
          onChange={(e) => {
            setDietary(e.target.value);
            setErrors((value) => ({ ...value, dietary: "" }));
          }}
          placeholder="Vegetarian, vegan…"
          aria-invalid={!!errors.dietary}
          aria-describedby={`dietary-help${errors.dietary ? " dietary-error" : ""}`}
        />
        <small id="dietary-help">Separate preferences with commas.</small>
        <FieldError id="dietary-error">{errors.dietary}</FieldError>
        <label htmlFor="allergens">Ingredients to exclude</label>
        <input
          id="allergens"
          value={allergens}
          onChange={(e) => {
            setAllergens(e.target.value);
            setErrors((value) => ({ ...value, allergens: "" }));
          }}
          placeholder="Peanut, sesame…"
          aria-invalid={!!errors.allergens}
          aria-describedby={`allergens-help${errors.allergens ? " allergens-error" : ""}`}
        />
        <small id="allergens-help">
          Use ingredient names, separated by commas. Review recipe ingredients
          before cooking.
        </small>
        <FieldError id="allergens-error">{errors.allergens}</FieldError>
        <button type="submit" className="primary">
          Save preferences
        </button>
        <p className="muted">
          Clear either field and save to remove its saved entries.
        </p>
      </form>
    </section>
  );
}

export default function PreferencesPage() {
  const { data, api, run } = useOutletContext();
  return <Preferences value={data.preferences} api={api} run={run} />;
}
