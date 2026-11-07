import EDWorkspaceCard from "./workspace-base-card";

const LitElement = Object.getPrototypeOf(
  customElements.get("ha-panel-lovelace")
);
const html = LitElement.prototype.html;
const css = LitElement.prototype.css;

class EDActivitesCard extends EDWorkspaceCard {
  getHtmlMode() {
    return "text";
  }

  getCardContent() {
    const workspaceContent = this.getWorkspaceContentOrLoading();
    if ("loading" in workspaceContent) {
      return workspaceContent.loading;
    }

    const { attributes } = workspaceContent;
    const activities = this.getLatestItems(
      attributes["Activités"],
      this.getLimit(this.config.max_activities, 5)
    );

    return html`<section>
      <h2>Activités</h2>
      ${activities.length
        ? activities.map((item) => this.getItem(item))
        : html`<p class="empty">Aucune activité</p>`}
    </section>`;
  }

  getDefaultConfig() {
    return {
      display_header: true,
      max_activities: 5,
    };
  }

  static getStubConfig() {
    return {
      display_header: true,
      max_activities: 5,
    };
  }

  static getConfigElement() {
    return document.createElement("ecole_directe-activites-card-editor");
  }

  static get styles() {
    return css`
      ${super.styles}
      h2 {
        margin: 12px 0 6px;
        font-size: 1em;
      }
      article {
        padding: 8px 0;
        border-top: 1px solid var(--divider-color);
      }
    `;
  }
}

customElements.define("ecole_directe-activites-card", EDActivitesCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "ecole_directe-activites-card",
  name: "Carte Activités Ecole Directe",
  description: "Affiche les dernières activités d'un espace de travail",
});
