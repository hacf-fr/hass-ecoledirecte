import EDWorkspaceCard from "./workspace-base-card";

const LitElement = Object.getPrototypeOf(
  customElements.get("ha-panel-lovelace")
);
const html = LitElement.prototype.html;
const css = LitElement.prototype.css;

class EDPostitsCard extends EDWorkspaceCard {
  getCardStyle(fullHtml) {
    return fullHtml ? "background-color: rgb(217, 237, 247);" : "";
  }

  getCardContent() {
    const workspaceContent = this.getWorkspaceContentOrLoading();
    if ("loading" in workspaceContent) {
      return workspaceContent.loading;
    }

    const { attributes } = workspaceContent;
    const postits = this.getLatestItems(
      attributes["Post-it"],
      this.getLimit(this.config.max_postits, 2)
    );

    return html`<section>
      ${postits.length
        ? postits.map((item) => this.getItem(item))
        : html`<p class="empty">Aucun post-it</p>`}
    </section>`;
  }

  getDefaultConfig() {
    return {
      display_header: true,
      max_postits: 2,
      allow_html: "text",
    };
  }

  static getStubConfig() {
    return {
      display_header: true,
      max_postits: 2,
      allow_html: "text",
    };
  }

  static getConfigElement() {
    return document.createElement("ecole_directe-postits-card-editor");
  }

  static get styles() {
    return css`
      ${super.styles}
      ha-card.full-html,
      ha-card.full-html * {
        color: #000 !important;
      }
      article {
        padding: 8px 0;
        border-top: 1px solid var(--divider-color);
      }
    `;
  }
}

customElements.define("ecole_directe-postits-card", EDPostitsCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "ecole_directe-postits-card",
  name: "Carte Post-it Ecole Directe",
  description: "Affiche les derniers post-it d'un espace de travail",
});
