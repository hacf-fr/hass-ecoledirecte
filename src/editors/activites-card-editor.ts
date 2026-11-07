import BaseEDCardEditor from "./base-editor";

const LitElement = Object.getPrototypeOf(
  customElements.get("ha-panel-lovelace")
);
const html = LitElement.prototype.html;
const css = LitElement.prototype.css;

class EDActivitesCardEditor extends BaseEDCardEditor {
  render() {
    if (!this.hass || !this._config) {
      return html``;
    }

    return html`
      ${this.buildEntityPickerField(
        "Espace de travail",
        "entity",
        this._config.entity,
        "(espace|workspace)"
      )}
      ${this.buildSwitchField(
        "Display header",
        "display_header",
        this._config.display_header,
        true
      )}
      ${this.buildNumberField(
        "Nombre d'activités",
        "max_activities",
        this._config.max_activities,
        5,
        1
      )}
    `;
  }

  static get styles() {
    return css`
      ${super.styles}
      .number-field {
        display: block;
        padding-top: 15px;
        color: var(--primary-text-color);
        font-size: 14px;
      }
      .number-field span {
        display: block;
        padding-bottom: 6px;
      }
      .number-field input {
        box-sizing: border-box;
        width: 100%;
        min-height: 40px;
        padding: 8px 12px;
        border: 1px solid var(--divider-color);
        border-radius: 4px;
        background: var(--card-background-color, var(--primary-background-color));
        color: var(--primary-text-color);
        font: inherit;
      }
    `;
  }
}

customElements.define(
  "ecole_directe-activites-card-editor",
  EDActivitesCardEditor
);
