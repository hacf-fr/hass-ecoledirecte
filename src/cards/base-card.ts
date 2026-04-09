const LitElement = Object.getPrototypeOf(
  customElements.get("ha-panel-lovelace")
) as typeof HTMLElement;
const html = (LitElement as any).prototype.html;
const css = (LitElement as any).prototype.css;

class BaseEDCard extends LitElement {
  [key: string]: any;

  static get properties() {
    return {
      config: {},
      hass: {},
      header_title: { type: String },
      no_data_message: { type: String },
    };
  }

  getCardHeader() {
    let child_attributes = this.hass.states[this.config.entity].attributes;
    if(child_attributes){
      let child_name =
        typeof child_attributes["prenom"] === "string" &&
        child_attributes["prenom"].length > 0
          ? child_attributes["prenom"]
          : child_attributes["nom_complet"];
      return html`<div class="ed-card-header">
        ${this.header_title} ${child_name}
      </div>`;
    }
    return html`<div class="ed-card-no-data">
      Veuillez choisir une autre entité
    </div>`;
  }

  noDataMessage() {
    return html`<div class="ed-card-no-data">${this.no_data_message}</div>`;
  }

  render() {
    if (!this.config || !this.hass) {
      return html`<div class="ed-card-no-data">
        Veuillez configurer la carte
      </div>`;
    }

    const stateObj = this.hass.states[this.config.entity];

    if (stateObj) {
      this.initCard();
      return html` <ha-card id="${this.config.entity}-card">
        ${this.config.display_header ? this.getCardHeader() : ""}
        ${this.getCardContent()}
      </ha-card>`;
    }
    return html`<div class="ed-card-no-data">
      Veuillez choisir une autre entité
    </div>`;
  }

  // Définit la configuration de la carte
  setConfig(config) {
    if (!config.entity) {
      throw new Error("Vous devez définir une entité");
    }

    this.config = {
      ...this.getDefaultConfig(),
      ...config,
    };
  }

  getItems() {
    let items = [];
    let entity_state = this.hass.states[this.config.entity];
    if (entity_state && entity_state.attributes[this.items_attribute_key]) {
      items.push(...entity_state.attributes[this.items_attribute_key]);
    }
    return items;
  }

  static get styles() {
    return css`
      .ed-card-header {
        text-align: center;
      }
      div {
        padding: 12px;
        font-weight: bold;
        font-size: 1em;
      }
      .ed-card-no-data {
        display: block;
        padding: 8px;
        text-align: center;
        font-style: italic;
      }
    `;
  }
}

export default BaseEDCard;
