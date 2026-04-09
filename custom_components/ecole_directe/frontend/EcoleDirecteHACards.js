var V=Object.getPrototypeOf(customElements.get("ha-panel-lovelace")),D=V.prototype.html,ze=V.prototype.css,U=class extends V{static get properties(){return{config:{},hass:{},header_title:{type:String},no_data_message:{type:String}}}getCardHeader(){let e=this.hass.states[this.config.entity].attributes;if(e){let t=typeof e.prenom=="string"&&e.prenom.length>0?e.prenom:e.nom_complet;return D`<div class="ed-card-header">
        ${this.header_title} ${t}
      </div>`}return D`<div class="ed-card-no-data">
      Veuillez choisir une autre entité
    </div>`}noDataMessage(){return D`<div class="ed-card-no-data">${this.no_data_message}</div>`}render(){return!this.config||!this.hass?D`<div class="ed-card-no-data">
        Veuillez configurer la carte
      </div>`:this.hass.states[this.config.entity]?(this.initCard(),D` <ha-card id="${this.config.entity}-card">
        ${this.config.display_header?this.getCardHeader():""}
        ${this.getCardContent()}
      </ha-card>`):D`<div class="ed-card-no-data">
      Veuillez choisir une autre entité
    </div>`}setConfig(e){if(!e.entity)throw new Error("Vous devez d\xE9finir une entit\xE9");this.config={...this.getDefaultConfig(),...e}}getItems(){let e=[],t=this.hass.states[this.config.entity];return t&&t.attributes[this.items_attribute_key]&&e.push(...t.attributes[this.items_attribute_key]),e}static get styles(){return ze`
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
    `}},_=U;var me=Object.getPrototypeOf(customElements.get("ha-panel-lovelace")),g=me.prototype.html,Ue=me.prototype.css;Date.prototype.getWeekNumber=function(){var r=new Date(+this);return r.setHours(0,0,0,0),r.setDate(r.getDate()+4-(r.getDay()||7)),Math.ceil(((r-new Date(r.getFullYear(),0,1))/864e5+1)/7)};function Ve(r,e){return r.getFullYear()===e.getFullYear()&&r.getMonth()===e.getMonth()&&r.getDate()===e.getDate()}var q=class extends _{constructor(){super(...arguments);this.lunchBreakRendered=!1}initCard(){}getBreakRow(t,i){return g` <tr class="lunch-break ${i?"lesson-ended":""}">
      <td></td>
      <td><span></span></td>
      <td colspan="2">
        <span class="lesson-name">${t}</span>
      </td>
    </tr>`}getTimetableRow(t){let i=new Date().getTime(),a=Date.parse(t.start_at),s=Date.parse(t.end_at),n=g``;this.config.display_lunch_break&&t.is_afternoon&&!this.lunchBreakRendered&&(n=this.getBreakRow("Repas",this.config.dim_ended_lessons&&a<i),this.lunchBreakRendered=!0);let o=g`
      <tr
        class="${t.is_annule?"lesson-canceled":""} ${this.config.dim_ended_lessons&&s<i?"lesson-ended":""}"
      >
        <td>
          ${t.start_time}<br />
          ${t.end_time}
        </td>
        <td>
          <span style="background-color:${t.background_color}"></span>
        </td>
        <td>
          <span class="lesson-name">${t.lesson}</span>
          ${this.config.display_classroom?g`<span class="lesson-classroom">
                ${t.salle?"Salle "+t.salle:""}
                ${t.salle&&this.config.display_teacher?", ":""}
              </span>`:""}
          ${this.config.display_teacher?g`<span class="lesson-teacher"> ${t.prof} </span>`:""}
        </td>
        <td>
          ${t.dispense?g`<span class="lesson-status">${t.dispense}</span>`:""}
        </td>
      </tr>
    `;return g`${n}${o}`}getFormattedDate(t){return new Date(t.start_at).toLocaleDateString("fr-FR",{weekday:"long",day:"2-digit",month:"2-digit"}).replace(/^(.)/,i=>i.toUpperCase())}getFormattedTime(t){return new Intl.DateTimeFormat("fr-FR",{hour:"numeric",minute:"numeric"}).format(new Date(t))}getDayHeader(t,i,a,s){return g`<div class="ed-timetable-header">
      ${this.config.enable_slider?g`<span
            class="ed-timetable-header-arrow-left ${s===0?"disabled":""}"
            @click=${n=>this.changeDay("previous",n)}
            >←</span
          >`:""}
      <span class="ed-timetable-header-date"
        >${this.getFormattedDate(t)}</span
      >
      ${this.config.display_day_hours&&i&&a?g`<span class="ed-timetable-header-hours">
            ${this.getFormattedTime(i)} -
            ${this.getFormattedTime(a)}
          </span>`:""}
      ${this.config.enable_slider?g`<span
            class="ed-timetable-header-arrow-right"
            @click=${n=>this.changeDay("next",n)}
            >→</span
          >`:""}
    </div>`}changeDay(t,i){if(i.preventDefault(),i.target.classList.contains("disabled"))return;let a=i.target.parentElement.parentElement,s=a.previousElementSibling&&a.previousElementSibling.classList.contains("ed-timetable-day-wrapper"),n=a.nextElementSibling&&a.nextElementSibling.classList.contains("ed-timetable-day-wrapper"),o=null;t==="previous"&&s?o=a.previousElementSibling:t==="next"&&n&&(o=a.nextElementSibling),o&&(a.classList.remove("active"),o.classList.add("active"),s=o.previousElementSibling&&o.previousElementSibling.classList.contains("ed-timetable-day-wrapper"),n=o.nextElementSibling&&o.nextElementSibling.classList.contains("ed-timetable-day-wrapper"),s||o.querySelector(".ed-timetable-header-arrow-left").classList.add("disabled"),n||o.querySelector(".ed-timetable-header-arrow-right").classList.add("disabled"))}render(){if(!this.config||!this.hass)return g`<div class="ed-card-no-data">
        Veuillez configurer la carte
      </div>`;let t=this.hass.states[this.config.entity];if(t){let i=t.attributes["Emploi du temps"];if(i){this.lunchBreakRendered=!1;let a=[],s=[],n=0,o=null,l=null,c=new Date,h=0;for(let d=0;d<i.length;d++){let p=i[d],y=this.getFormattedDate(p),w=new Date(p.end_at);if(p.isAnnule||(o===null&&(o=p.start_at),l=p.end_at),p.isAnnule&&d<i.length-1){let P=i[d+1];if(p.start_at===P.start_at&&!P.isAnnule)continue}if(s.push(this.getTimetableRow(p)),d+1>=i.length||d+1<i.length&&y!==this.getFormattedDate(i[d+1]))this.config.enable_slider&&this.config.switch_to_next_day&&Ve(w,c)&&w<c&&(h=n+1),a.push(g`
              <div
                class="${this.config.enable_slider?"slider-enabled":""} ed-timetable-day-wrapper ${n===h?"active":""}"
              >
                ${this.getDayHeader(p,o,l,n)}
                <table>
                  ${s}
                </table>
              </div>
            `),s=[],this.lunchBreakRendered=!1,o=null,l=null,n++;else if(this.config.display_free_time_slots&&d+1<i.length){let P=new Date(p.end_at),ue=i[d+1],ge=new Date(ue.start_at);if(p.is_morning===ue.is_morning&&Math.floor((ge-P)/1e3/60)>30){let Ie=new Date;s.push(this.getBreakRow("Pas de cours",this.config.dim_ended_lessons&&ge<Ie))}}}return s.length>0&&a.push(g`<table>
              ${s}
            </table>`),g` <ha-card
          id="${this.config.entity}-card"
          class="${this.config.enable_slider?"ed-timetable-card-slider":""}"
        >
          ${this.config.display_header?this.getCardHeader():""}
          ${a}
        </ha-card>`}}return g`<div class="ed-card-no-data">
      Veuillez choisir une autre entité
    </div>`}setConfig(t){if(!t.entity)throw new Error("Vous devez d\xE9finir une entit\xE9");let i={entity:null,display_header:!0,display_classroom:!0,display_teacher:!0,display_day_hours:!0,display_lunch_break:!0,dim_ended_lessons:!0,enable_slider:!1,switch_to_next_day:!1,display_free_time_slots:!0};this.config={...i,...t},this.header_title="Emploi du temps de ",this.no_data_message="Pas d'emploi du temps \xE0 afficher"}static get styles(){return Ue`
      ${super.styles}
      .ed-timetable-card-slider .ed-timetable-day-wrapper {
        display: none;
      }
      .ed-timetable-card-slider .ed-timetable-day-wrapper.active {
        display: block;
      }
      .ed-timetable-card-slider .ed-timetable-header-date {
        display: inline-block;
        text-align: center;
        width: 120px;
      }
      .ed-timetable-header-arrow-left,
      .ed-timetable-header-arrow-right {
        cursor: pointer;
      }
      .ed-timetable-header-arrow-left.disabled,
      .ed-timetable-header-arrow-right.disabled {
        opacity: 0.3;
        pointer-events: none;
      }
      span.ed-timetable-header-hours {
        float: right;
      }
      table {
        clear: both;
        font-size: 0.9em;
        font-family: Roboto;
        width: 100%;
        outline: 0px solid #393c3d;
        border-collapse: collapse;
      }
      tr:nth-child(odd) {
        background-color: rgba(0, 0, 0, 0.1);
      }
      td {
        vertical-align: middle;
        padding: 5px 10px 5px 10px;
        text-align: left;
      }
      tr td:first-child {
        width: 13%;
        text-align: right;
      }
      span.lesson-name {
        font-weight: bold;
        display: block;
      }
      tr td:nth-child(2) {
        width: 4px;
        padding: 5px 0;
      }
      tr td:nth-child(2) > span {
        display: inline-block;
        width: 4px;
        height: 3rem;
        border-radius: 4px;
        background-color: grey;
        margin-top: 4px;
      }
      span.lesson-status {
        color: white;
        background-color: rgb(75, 197, 253);
        padding: 4px;
        border-radius: 4px;
      }
      .lesson-canceled span.lesson-name {
        text-decoration: line-through;
      }
      .lesson-canceled span.lesson-status {
        background-color: rgb(250, 50, 75);
      }
      .lesson-ended {
        opacity: 0.3;
      }
      div:not(.slider-enabled).ed-timetable-day-wrapper
        + div:not(.slider-enabled).ed-timetable-day-wrapper {
        border-top: 1px solid white;
      }
    `}static getStubConfig(){return{display_header:!0,display_lunch_break:!0,display_classroom:!0,display_teacher:!0,display_day_hours:!0,dim_ended_lessons:!0,enable_slider:!1,display_free_time_slots:!0,switch_to_next_day:!1}}static getConfigElement(){return document.createElement("ecole_directe-emploi_temps-card-editor")}};customElements.define("ecole_directe-emploi_temps-card",q);window.customCards=window.customCards||[];window.customCards.push({type:"ecole_directe-emploi_temps-card",name:"Carte de l'emploi du temps pour Ecole Directe",description:"Affiche l'emploi du temps pour Ecole Directe",documentationURL:"https://github.com/hacf-fr/EcoleDirecteHACards?tab=readme-ov-file#emploi_temps"});var T=globalThis,_e=r=>r,N=T.trustedTypes,fe=N?N.createPolicy("lit-html",{createHTML:r=>r}):void 0,xe="$lit$",v=`lit$${Math.random().toFixed(9).slice(2)}$`,Ae="?"+v,qe=`<${Ae}>`,E=document,B=()=>E.createComment(""),H=r=>r===null||typeof r!="object"&&typeof r!="function",K=Array.isArray,We=r=>K(r)||typeof r?.[Symbol.iterator]=="function",W=`[ 	
\f\r]`,L=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,ye=/-->/g,ve=/>/g,x=RegExp(`>|${W}(?:([^\\s"'>=/]+)(${W}*=${W}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`,"g"),be=/'/g,$e=/"/g,Ee=/^(?:script|style|textarea|title)$/i,Q=r=>(e,...t)=>({_$litType$:r,strings:e,values:t}),dt=Q(1),ct=Q(2),ht=Q(3),C=Symbol.for("lit-noChange"),u=Symbol.for("lit-nothing"),we=new WeakMap,A=E.createTreeWalker(E,129);function Ce(r,e){if(!K(r)||!r.hasOwnProperty("raw"))throw Error("invalid template strings array");return fe!==void 0?fe.createHTML(e):e}var Ye=(r,e)=>{let t=r.length-1,i=[],a,s=e===2?"<svg>":e===3?"<math>":"",n=L;for(let o=0;o<t;o++){let l=r[o],c,h,d=-1,p=0;for(;p<l.length&&(n.lastIndex=p,h=n.exec(l),h!==null);)p=n.lastIndex,n===L?h[1]==="!--"?n=ye:h[1]!==void 0?n=ve:h[2]!==void 0?(Ee.test(h[2])&&(a=RegExp("</"+h[2],"g")),n=x):h[3]!==void 0&&(n=x):n===x?h[0]===">"?(n=a??L,d=-1):h[1]===void 0?d=-2:(d=n.lastIndex-h[2].length,c=h[1],n=h[3]===void 0?x:h[3]==='"'?$e:be):n===$e||n===be?n=x:n===ye||n===ve?n=L:(n=x,a=void 0);let y=n===x&&r[o+1].startsWith("/>")?" ":"";s+=n===L?l+qe:d>=0?(i.push(c),l.slice(0,d)+xe+l.slice(d)+v+y):l+v+(d===-2?o:y)}return[Ce(r,s+(r[t]||"<?>")+(e===2?"</svg>":e===3?"</math>":"")),i]},O=class r{constructor({strings:e,_$litType$:t},i){let a;this.parts=[];let s=0,n=0,o=e.length-1,l=this.parts,[c,h]=Ye(e,t);if(this.el=r.createElement(c,i),A.currentNode=this.el.content,t===2||t===3){let d=this.el.content.firstChild;d.replaceWith(...d.childNodes)}for(;(a=A.nextNode())!==null&&l.length<o;){if(a.nodeType===1){if(a.hasAttributes())for(let d of a.getAttributeNames())if(d.endsWith(xe)){let p=h[n++],y=a.getAttribute(d).split(v),w=/([.?@])?(.*)/.exec(p);l.push({type:1,index:s,name:w[2],strings:y,ctor:w[1]==="."?G:w[1]==="?"?X:w[1]==="@"?Z:F}),a.removeAttribute(d)}else d.startsWith(v)&&(l.push({type:6,index:s}),a.removeAttribute(d));if(Ee.test(a.tagName)){let d=a.textContent.split(v),p=d.length-1;if(p>0){a.textContent=N?N.emptyScript:"";for(let y=0;y<p;y++)a.append(d[y],B()),A.nextNode(),l.push({type:2,index:++s});a.append(d[p],B())}}}else if(a.nodeType===8)if(a.data===Ae)l.push({type:2,index:s});else{let d=-1;for(;(d=a.data.indexOf(v,d+1))!==-1;)l.push({type:7,index:s}),d+=v.length-1}s++}}static createElement(e,t){let i=E.createElement("template");return i.innerHTML=e,i}};function k(r,e,t=r,i){if(e===C)return e;let a=i!==void 0?t._$Co?.[i]:t._$Cl,s=H(e)?void 0:e._$litDirective$;return a?.constructor!==s&&(a?._$AO?.(!1),s===void 0?a=void 0:(a=new s(r),a._$AT(r,t,i)),i!==void 0?(t._$Co??(t._$Co=[]))[i]=a:t._$Cl=a),a!==void 0&&(e=k(r,a._$AS(r,e.values),a,i)),e}var Y=class{constructor(e,t){this._$AV=[],this._$AN=void 0,this._$AD=e,this._$AM=t}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(e){let{el:{content:t},parts:i}=this._$AD,a=(e?.creationScope??E).importNode(t,!0);A.currentNode=a;let s=A.nextNode(),n=0,o=0,l=i[0];for(;l!==void 0;){if(n===l.index){let c;l.type===2?c=new I(s,s.nextSibling,this,e):l.type===1?c=new l.ctor(s,l.name,l.strings,this,e):l.type===6&&(c=new J(s,this,e)),this._$AV.push(c),l=i[++o]}n!==l?.index&&(s=A.nextNode(),n++)}return A.currentNode=E,a}p(e){let t=0;for(let i of this._$AV)i!==void 0&&(i.strings!==void 0?(i._$AI(e,i,t),t+=i.strings.length-2):i._$AI(e[t])),t++}},I=class r{get _$AU(){return this._$AM?._$AU??this._$Cv}constructor(e,t,i,a){this.type=2,this._$AH=u,this._$AN=void 0,this._$AA=e,this._$AB=t,this._$AM=i,this.options=a,this._$Cv=a?.isConnected??!0}get parentNode(){let e=this._$AA.parentNode,t=this._$AM;return t!==void 0&&e?.nodeType===11&&(e=t.parentNode),e}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(e,t=this){e=k(this,e,t),H(e)?e===u||e==null||e===""?(this._$AH!==u&&this._$AR(),this._$AH=u):e!==this._$AH&&e!==C&&this._(e):e._$litType$!==void 0?this.$(e):e.nodeType!==void 0?this.T(e):We(e)?this.k(e):this._(e)}O(e){return this._$AA.parentNode.insertBefore(e,this._$AB)}T(e){this._$AH!==e&&(this._$AR(),this._$AH=this.O(e))}_(e){this._$AH!==u&&H(this._$AH)?this._$AA.nextSibling.data=e:this.T(E.createTextNode(e)),this._$AH=e}$(e){let{values:t,_$litType$:i}=e,a=typeof i=="number"?this._$AC(e):(i.el===void 0&&(i.el=O.createElement(Ce(i.h,i.h[0]),this.options)),i);if(this._$AH?._$AD===a)this._$AH.p(t);else{let s=new Y(a,this),n=s.u(this.options);s.p(t),this.T(n),this._$AH=s}}_$AC(e){let t=we.get(e.strings);return t===void 0&&we.set(e.strings,t=new O(e)),t}k(e){K(this._$AH)||(this._$AH=[],this._$AR());let t=this._$AH,i,a=0;for(let s of e)a===t.length?t.push(i=new r(this.O(B()),this.O(B()),this,this.options)):i=t[a],i._$AI(s),a++;a<t.length&&(this._$AR(i&&i._$AB.nextSibling,a),t.length=a)}_$AR(e=this._$AA.nextSibling,t){for(this._$AP?.(!1,!0,t);e!==this._$AB;){let i=_e(e).nextSibling;_e(e).remove(),e=i}}setConnected(e){this._$AM===void 0&&(this._$Cv=e,this._$AP?.(e))}},F=class{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(e,t,i,a,s){this.type=1,this._$AH=u,this._$AN=void 0,this.element=e,this.name=t,this._$AM=a,this.options=s,i.length>2||i[0]!==""||i[1]!==""?(this._$AH=Array(i.length-1).fill(new String),this.strings=i):this._$AH=u}_$AI(e,t=this,i,a){let s=this.strings,n=!1;if(s===void 0)e=k(this,e,t,0),n=!H(e)||e!==this._$AH&&e!==C,n&&(this._$AH=e);else{let o=e,l,c;for(e=s[0],l=0;l<s.length-1;l++)c=k(this,o[i+l],t,l),c===C&&(c=this._$AH[l]),n||(n=!H(c)||c!==this._$AH[l]),c===u?e=u:e!==u&&(e+=(c??"")+s[l+1]),this._$AH[l]=c}n&&!a&&this.j(e)}j(e){e===u?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,e??"")}},G=class extends F{constructor(){super(...arguments),this.type=3}j(e){this.element[this.name]=e===u?void 0:e}},X=class extends F{constructor(){super(...arguments),this.type=4}j(e){this.element.toggleAttribute(this.name,!!e&&e!==u)}},Z=class extends F{constructor(e,t,i,a,s){super(e,t,i,a,s),this.type=5}_$AI(e,t=this){if((e=k(this,e,t,0)??u)===C)return;let i=this._$AH,a=e===u&&i!==u||e.capture!==i.capture||e.once!==i.once||e.passive!==i.passive,s=e!==u&&(i===u||a);a&&this.element.removeEventListener(this.name,this,i),s&&this.element.addEventListener(this.name,this,e),this._$AH=e}handleEvent(e){typeof this._$AH=="function"?this._$AH.call(this.options?.host??this.element,e):this._$AH.handleEvent(e)}},J=class{constructor(e,t,i){this.element=e,this.type=6,this._$AN=void 0,this._$AM=t,this.options=i}get _$AU(){return this._$AM._$AU}_$AI(e){k(this,e)}};var Ge=T.litHtmlPolyfillSupport;Ge?.(O,I),(T.litHtmlVersions??(T.litHtmlVersions=[])).push("3.3.2");var De={ATTRIBUTE:1,CHILD:2,PROPERTY:3,BOOLEAN_ATTRIBUTE:4,EVENT:5,ELEMENT:6},ke=r=>(...e)=>({_$litDirective$:r,values:e}),z=class{constructor(e){}get _$AU(){return this._$AM._$AU}_$AT(e,t,i){this._$Ct=e,this._$AM=t,this._$Ci=i}_$AS(e,t){return this.update(e,t)}update(e,t){return this.render(...t)}};var j=class extends z{constructor(e){if(super(e),this.it=u,e.type!==De.CHILD)throw Error(this.constructor.directiveName+"() can only be used in child bindings")}render(e){if(e===u||e==null)return this._t=void 0,this.it=e;if(e===C)return e;if(typeof e!="string")throw Error(this.constructor.directiveName+"() called with a non-string value");if(e===this.it)return this._t;this.it=e;let t=[e];return t.raw=t,this._t={_$litType$:this.constructor.resultType,strings:t,values:[]}}};j.directiveName="unsafeHTML",j.resultType=1;var Fe=ke(j);var Se=Object.getPrototypeOf(customElements.get("ha-panel-lovelace")),m=Se.prototype.html,Xe=Se.prototype.css;Date.prototype.getWeekNumber=function(){var r=new Date(+this);return r.setHours(0,0,0,0),r.setDate(r.getDate()+4-(r.getDay()||7)),Math.ceil(((r-new Date(r.getFullYear(),0,1))/864e5+1)/7)};var ee=class extends _{constructor(){super(...arguments);this.lunchBreakRendered=!1}initCard(){}getFormattedDate(t){return new Date(t).toLocaleDateString("fr-FR",{weekday:"long",day:"2-digit",month:"2-digit"}).replace(/^(.)/,i=>i.toUpperCase())}getDayHeader(t,i){return m`<div class="ed-devoir-header">
      ${this.config.enable_slider?m`<span
            class="ed-devoir-header-arrow-left ${i===0?"disabled":""}"
            @click=${a=>this.changeDay("previous",a)}
            >←</span
          >`:""}
      <span class="ed-devoir-header-date"
        >${this.getFormattedDate(t.date)}</span
      >
      ${this.config.enable_slider?m`<span
            class="ed-devoir-header-arrow-right"
            @click=${a=>this.changeDay("next",a)}
            >→</span
          >`:""}
    </div>`}changeDay(t,i){if(i.preventDefault(),i.target.classList.contains("disabled"))return;let a=i.target.parentElement.parentElement,s=a.previousElementSibling&&a.previousElementSibling.classList.contains("ed-devoir-day-wrapper"),n=a.nextElementSibling&&a.nextElementSibling.classList.contains("ed-devoir-day-wrapper"),o=null;t==="previous"&&s?o=a.previousElementSibling:t==="next"&&n&&(o=a.nextElementSibling),o&&(a.classList.remove("active"),o.classList.add("active"),s=o.previousElementSibling&&o.previousElementSibling.classList.contains("ed-devoir-day-wrapper"),n=o.nextElementSibling&&o.nextElementSibling.classList.contains("ed-devoir-day-wrapper"),s||o.querySelector(".ed-devoir-header-arrow-left").classList.add("disabled"),n||o.querySelector(".ed-devoir-header-arrow-right").classList.add("disabled"))}getdevoirRow(t,i){let a=t.description.trim().replace(`
`,"<br />");return m`
      <tr class="${t.effectue?"devoir-done":""}">
        <td class="devoir-detail">
          <label for="devoir-${i}">
            <span class="devoir-subject">${t.matiere}</span>
            ${t.interrogation?m`<span class="devoir-controle">(Contrôle)</span>`:m``}
          </label>
          <input type="checkbox" id="devoir-${i}" />
          <span class="devoir-description">${Fe(a)}</span>
        </td>
        <td class="devoir-status">
          <span
            >${t.effectue?m`<ha-icon icon="mdi:check"></ha-icon>`:m`<ha-icon icon="mdi:account-clock"></ha-icon>`}</span
          >
        </td>
      </tr>
    `}getDayRow(t,i,a){return m`
      <div
        class="${this.config.enable_slider?"slider-enabled":""} ed-devoir-day-wrapper ${a===0?"active":""}"
      >
        ${this.getDayHeader(t,a)}
        <table class="${this.config.reduce_done_devoir?"reduce-done":""}">
          ${i}
        </table>
      </div>
    `}render(){if(!this.config||!this.hass)return m`<div class="ed-card-no-data">
        Veuillez configurer la carte
      </div>`;let t=this.hass.states[this.config.entity];if(t){let i=t.attributes.Devoirs;if(i){let a=[],s=[],n=0;if(i&&i.length>0){if(i[0].Erreur)return m`<div class="ed-card-no-data">${i[0].Erreur}</div>`;let o=this.getFormattedDate(i[0].date);for(let l=0;l<i.length;l++){let c=i[l],h=this.getFormattedDate(c.date);c.effectue===!0&&this.config.display_done_devoir===!1||(o!==h&&(s.length>0&&(a.push(this.getDayRow(i[l-1],s,n)),s=[]),o=h,n++),s.push(this.getdevoirRow(c,l)))}s.length>0&&a.push(this.getDayRow(i[i.length-1],s,n))}return a.length===0&&a.push(this.noDataMessage()),m` <ha-card
          id="${this.config.entity}-card"
          class="${this.config.enable_slider?"ed-devoir-card-slider":""}"
        >
          ${this.config.display_header?this.getCardHeader():""}
          ${a}
        </ha-card>`}}return m`<div class="ed-card-no-data">
      Veuillez choisir une autre entité
    </div>`}setConfig(t){if(!t.entity)throw new Error("Vous devez d\xE9finir une entit\xE9");let i={entity:null,display_header:!0,reduce_done_devoir:!0,display_done_devoir:!0,enable_slider:!1};this.config={...i,...t},this.header_title="Devoirs de ",this.no_data_message="Pas de devoirs \xE0 faire"}static get styles(){return Xe`
      ${super.styles}
      .ed-devoir-card-slider .ed-devoir-day-wrapper {
        display: none;
      }
      .ed-devoir-card-slider .ed-devoir-day-wrapper.active {
        display: block;
      }
      .ed-devoir-card-slider .ed-devoir-header-date {
        display: inline-block;
        text-align: center;
        width: 120px;
      }
      .ed-devoir-header-arrow-left,
      .ed-devoir-header-arrow-right {
        cursor: pointer;
      }
      .ed-devoir-header-arrow-left.disabled,
      .ed-devoir-header-arrow-right.disabled {
        opacity: 0.3;
        pointer-events: none;
      }
      div:not(.slider-enabled) > .ed-devoir-header {
        border-bottom: 2px solid grey;
      }
      .slider-enabled > .ed-devoir-header {
        padding-top: 0;
        text-align: center;
      }
      table {
        font-size: 0.9em;
        font-family: Roboto;
        width: 100%;
        outline: 0px solid #393c3d;
        border-collapse: collapse;
      }
      td {
        vertical-align: top;
        padding: 5px 10px 5px 10px;
        padding-top: 8px;
        text-align: left;
      }
      td.devoir-detail {
        padding: 0;
        padding-top: 8px;
        padding-bottom: 8px;
      }
      span.devoir-subject {
        display: block;
        font-weight: bold;
      }
      span.devoir-controle {
        display: block;
        font-weight: bold;
        color: red;
      }
      span.devoir-description {
        font-size: 0.9em;
      }
      td.devoir-status {
        width: 5%;
      }
      .reduce-done .devoir-done label:hover {
        cusor: pointer;
      }
      .reduce-done .devoir-done .devoir-description {
        display: none;
      }
      .reduce-done .devoir-done input:checked + .devoir-description {
        display: block;
      }
      .devoir-detail input {
        display: none;
      }
    `}static getStubConfig(){return{display_header:!0,reduce_done_devoir:!0,display_done_devoir:!0,enable_slider:!1}}static getConfigElement(){return document.createElement("ecole_directe-devoirs-card-editor")}};customElements.define("ecole_directe-devoirs-card",ee);window.customCards=window.customCards||[];window.customCards.push({type:"ecole_directe-devoirs-card",name:"Carte des devoirs pour Ecole Directe",description:"Affiche les devoirs pour Ecole Directe",documentationURL:"https://github.com/hacf-fr/EcoleDirecteHACards?tab=readme-ov-file#devoirs"});var Re=Object.getPrototypeOf(customElements.get("ha-panel-lovelace")),b=Re.prototype.html,Ze=Re.prototype.css,te=class extends _{initCard(){this.items_attribute_key="notes",this.header_title="Notes de ",this.no_data_message="Aucune note disponible"}getFormattedDate(e){return new Date(e).toLocaleDateString("fr-FR",{weekday:"short",day:"2-digit",month:"2-digit"}).replace(/^(.)/,t=>t.toUpperCase())}getGradeRow(e){let t=parseFloat(e.note.replace(",",".")),i=[];if(this.config.compare_with_ratio!==null){let s=parseFloat(this.config.compare_with_ratio),n=t/parseFloat(e.sur.replace(",","."));i.push(n>=s?"above-ratio":"below-ratio")}else if(this.config.compare_with_class_average&&e.moyenne_classe){let s=parseFloat(e.moyenne_classe.replace(",","."));i.push(t>s?"above-average":"below-average")}let a=e.note_sur;if(this.config.grade_format==="short"&&(a=e.note),this.config.display_new_grade_notice){let s=new Date(e.date),n=new Date;s.getFullYear()===n.getFullYear()&&s.getMonth()===n.getMonth()&&s.getDate()===n.getDate()&&i.push("new-grade")}return b`
      <tr class="${i.join(" ")}">
        <td class="grade-color"><span></span></td>
        <td class="grade-description">
          <span class="grade-subject">${e.matiere}</span>
          ${this.config.display_comment?b`<span class="grade-comment">${e.commentaire}</span>`:""}
          ${this.config.display_date?b`<span class="grade-date"
                >${this.getFormattedDate(e.date)}</span
              >`:""}
          ${this.config.display_coefficient&&e.coefficient?b`<span class="grade-coefficient"
                >Coef. ${e.coefficient}</span
              >`:""}
        </td>
        <td class="grade-detail">
          <span class="grade-value">${a}</span>
          ${this.config.display_class_average&&e.moyenne_classe?b`<span class="grade-class-average"
                >Moy. ${e.moyenne_classe}</span
              >`:""}
          ${this.config.display_class_min&&e.min?b`<span class="grade-class-min">Min. ${e.min}</span>`:""}
          ${this.config.display_class_max&&e.max?b`<span class="grade-class-max">Max. ${e.max}</span>`:""}
        </td>
      </tr>
    `}getCardContent(){if(this.hass.states[this.config.entity]){let t=this.getItems(),i=this.config.max_grades??t.length,a=[],s=[];for(let n=0;n<i&&!(n>=t.length);n++){let o=t[n];a.push(this.getGradeRow(o))}return a.length>0?s.push(b`<table>
            ${a}
          </table>`):s.push(this.noDataMessage()),s}}getDefaultConfig(){return{grade_format:"full",display_header:!0,display_date:!0,display_comment:!0,display_class_average:!0,compare_with_class_average:!0,compare_with_ratio:null,display_coefficient:!0,display_class_min:!0,display_class_max:!0,display_new_grade_notice:!0,max_grades:null}}static get styles(){return Ze`
      ${super.styles}
      table {
        font-size: 0.9em;
        font-family: Roboto;
        width: 100%;
        outline: 0px solid #393c3d;
        border-collapse: collapse;
      }
      td {
        vertical-align: top;
        padding: 5px 10px 5px 10px;
        padding-top: 8px;
        text-align: left;
      }
      td.grade-color {
        width: 4px;
        padding-top: 11px;
      }
      td.grade-color > span {
        display: inline-block;
        width: 4px;
        height: 1rem;
        border-radius: 4px;
        background-color: grey;
      }
      .above-average .grade-color > span,
      .above-ratio .grade-color > span {
        background-color: green;
      }
      .below-average .grade-color > span,
      .below-ratio .grade-color > span {
        background-color: orange;
      }
      .grade-description {
        padding-left: 0;
      }
      .grade-subject {
        display: inline-block;
        font-weight: bold;
        position: relative;
      }
      .new-grade .grade-subject:after {
        content: " ";
        display: block;
        width: 6px;
        height: 6px;
        border-radius: 6px;
        background-color: orange;
        position: absolute;
        top: 6px;
        right: -14px;
      }
      .grade-comment {
        display: block;
      }
      .grade-date,
      .grade-coefficient {
        font-size: 0.9em;
        color: gray;
      }
      .grade-date + .grade-coefficient:before {
        content: " - ";
      }
      .grade-detail {
        text-align: right;
      }
      .grade-value {
        font-weight: bold;
      }
      .grade-value,
      .grade-class-average {
        display: block;
      }
      .grade-class-average,
      .grade-class-min,
      .grade-class-max {
        font-size: 0.9em;
        color: gray;
      }
      .grade-class-min + .grade-class-max:before {
        content: " - ";
      }
    `}static getStubConfig(){return{grade_format:"full",display_header:!0,display_date:!0,display_comment:!0,display_class_average:!0,compare_with_class_average:!0,compare_with_ratio:null,display_coefficient:!0,display_class_min:!0,display_class_max:!0,display_new_grade_notice:!0,max_grades:null}}static getConfigElement(){return document.createElement("ecole_directe-notes-card-editor")}};customElements.define("ecole_directe-notes-card",te);window.customCards=window.customCards||[];window.customCards.push({type:"ecole_directe-notes-card",name:"Carte des notes pour Ecole Directe",description:"Affiche les notes pour Ecole Directe",documentationURL:"https://github.com/hacf-fr/EcoleDirecteHACards?tab=readme-ov-file#notes"});var Le=Object.getPrototypeOf(customElements.get("ha-panel-lovelace")),$=Le.prototype.html,Je=Le.prototype.css,ie=class extends _{initCard(){this.items_attribute_key="Disciplines",this.header_title="Moyennes de ",this.no_data_message="Aucune moyenne"}getOverallAverageRow(){let e=`${this.config.entity}`;if(!this.hass.states[e])return $``;let t=this.hass.states[e].state;if(!t)return $``;let i=parseFloat(t.replace(",",".")),a=[];if(this.config.compare_with_ratio!==null){let s=parseFloat(this.config.compare_with_ratio);a.push(i>=s?"above-ratio":"below-ratio")}return $`
      <tr class="${a.join(" ")} overall-average">
        <td class="average-color"><span></span></td>
        <td class="average-description">
          <span class="average-subject">Moyenne générale</span>
        </td>
        <td class="average-detail">
          <span class="average-value"
            ><span>${t.replace(".",",")}</span></span
          >
        </td>
      </tr>
    `}getAverageRow(e){let t=parseFloat(e.moyenne.replace(",",".")),i=[];if(this.config.compare_with_ratio!==null){let a=parseFloat(this.config.compare_with_ratio);i.push(t>=a?"above-ratio":"below-ratio")}else if(this.config.compare_with_class_average&&e.moyenneClasse){let a=parseFloat(e.moyenneClasse.replace(",","."));i.push(t>a?"above-average":"below-average")}return $`
      <tr class="${i.join(" ")}">
        <td class="average-color">
          <span style="background-color:Grey"></span>
        </td>
        <td class="average-description">
          <span class="average-subject">${e.nom}</span>
        </td>
        <td class="average-detail">
          <span class="average-value">${e.moyenne}</span>
          ${this.config.display_class_average&&e.moyenneClasse?$`<span class="average-class-average"
                >Classe ${e.moyenneClasse}</span
              >`:""}
          ${this.config.display_class_min&&e.moyenneMin?$`<span class="average-class-min"
                >Min. ${e.moyenneMin}</span
              >`:""}
          ${this.config.display_class_max&&e.moyenneMax?$`<span class="average-class-max"
                >Max. ${e.moyenneMax}</span
              >`:""}
        </td>
      </tr>
    `}getCardContent(){if(this.hass.states[this.config.entity]){let t=this.getItems(),i=[],a=[];this.config.display_overall_average&&a.push(this.getOverallAverageRow());for(let s=0;s<t.length;s++){let n=t[s];a.push(this.getAverageRow(n))}return a.length>0?i.push($`<table>
            ${a}
          </table>`):i.push(this.noDataMessage()),i}return[]}getDefaultConfig(){return{display_header:!0,display_class_average:!0,compare_with_class_average:!0,compare_with_ratio:null,display_class_min:!0,display_class_max:!0,display_overall_average:!0}}static get styles(){return Je`
      ${super.styles}
      table {
        font-size: 0.9em;
        font-family: Roboto;
        width: 100%;
        outline: 0px solid #393c3d;
        border-collapse: collapse;
      }
      td {
        vertical-align: top;
        padding: 5px 10px 5px 10px;
        padding-top: 8px;
        text-align: left;
      }
      tr.overall-average {
        border-bottom: 1px solid #393c3d;
      }
      tr.overall-average td {
        text-transform: uppercase;
        padding-bottom: 10px;
      }
      tr.overall-average .average-value span {
        padding: 5px;
        border-radius: 5px;
        border: 1px solid var(--primary-text-color);
      }
      tr.overall-average tr td {
        padding-top: 10px;
      }
      td.average-comparison-color,
      td.average-color {
        width: 4px;
        padding-top: 11px;
      }
      td.average-comparison-color > span,
      td.average-color > span {
        display: inline-block;
        width: 4px;
        height: 1rem;
        border-radius: 4px;
        background-color: grey;
      }

      .above-average .average-detail,
      .above-ratio .average-detail,
      .below-average .average-detail,
      .below-ratio .average-detail {
        position: relative;
      }
      .above-average span.average-value,
      .above-ratio span.average-value,
      .below-average span.average-value,
      .below-ratio span.average-value {
        padding-right: 16px;
      }
      .above-average span.average-value:before,
      .above-ratio span.average-value:before,
      .below-average span.average-value:before,
      .below-ratio span.average-value:before {
        content: " ";
        display: block;
        width: 10px;
        height: 10px;
        border-radius: 5px;
        position: absolute;
        right: 10px;
        top: 13px;
      }
      .above-average span.average-value:before,
      .above-ratio span.average-value:before {
        background-color: green;
      }
      .below-average span.average-value:before,
      .below-ratio span.average-value:before {
        background-color: orange;
      }
      .average-description {
        padding-left: 0;
      }
      .average-subject {
        display: inline-block;
        font-weight: bold;
        position: relative;
      }
      .average-detail {
        text-align: right;
      }
      .average-value {
        font-weight: bold;
      }
      .average-value,
      .average-class-average {
        display: block;
      }
      .average-class-average,
      .average-class-min,
      .average-class-max {
        font-size: 0.9em;
        color: gray;
      }
      .average-class-min + .average-class-max:before {
        content: " - ";
      }
    `}static getStubConfig(){return{display_header:!0,display_class_average:!0,compare_with_class_average:!0,compare_with_ratio:null,display_class_min:!0,display_class_max:!0}}static getConfigElement(){return document.createElement("ecole_directe-moyennes-card-editor")}};customElements.define("ecole_directe-moyennes-card",ie);window.customCards=window.customCards||[];window.customCards.push({type:"ecole_directe-moyennes-card",name:"Carte des moyennes pour Ecole Directe",description:"Affiche les moyennes pour Ecole Directe",documentationURL:"https://github.com/hacf-fr/EcoleDirecteHACards?tab=readme-ov-file#moyennes"});var Te=Object.getPrototypeOf(customElements.get("ha-panel-lovelace")),S=Te.prototype.html,Ke=Te.prototype.css,ae=class extends _{initCard(){this.items_attribute_key="Evaluations",this.header_title="Evaluations de ",this.no_data_message="Pas d'\xE9valuation \xE0 afficher"}getFormattedDate(e){return new Date(e).toLocaleDateString("fr-FR",{weekday:"short",day:"2-digit",month:"2-digit"}).replace(/^(.)/,t=>t.toUpperCase())}getAcquisitionRow(e){return S`<tr class="acquisition-row">
      <td>${e.competence}</td>
      <td>${this.getAcquisitionIcon(e)}</td>
    </tr>`}getAcquisitionIcon(e){let t=this.config.mapping_evaluations[e.valeur]||e.valeur,i="";return t==="A+"?i="+":t==="Abs"&&(i="a"),S`
      <span
        title="${e.descriptif}"
        class="acquisition-icon acquisition-icon-${t}"
      >
        ${i}
      </span>
    `}getEvaluationRow(e,t){let i=e.elements_programme,a=[],s=[],n="grey";for(let o=0;o<i.length;o++)a.push(this.getAcquisitionIcon(i[o])),s.push(this.getAcquisitionRow(i[o]));return S`
      <tr class="evaluation-row">
        <td class="evaluation-color">
          <span style="background-color:${n}"></span>
        </td>
        <td class="evaluation-description">
          <label for="evaluation-full-detail-${t}">
            <span class="evaluation-subject">${e.matiere}</span>
          </label>
          <input type="checkbox" id="evaluation-full-detail-${t}" />
          ${this.config.display_comment?S`<span class="evaluation-comment">${e.devoir}</span>`:""}
          ${this.config.display_date?S`<span class="evaluation-date"
                >${this.getFormattedDate(e.date)}</span
              >`:""}
        </td>
        <td class="evaluation-detail">${a}</td>
      </tr>
      ${s}
    `}getCardContent(){if(this.hass.states[this.config.entity]){let t=this.getItems(),i=this.config.max_evaluations??t.length,a=[],s=[];for(let n=0;n<i&&!(n>=t.length);n++){let o=t[n];a.push(this.getEvaluationRow(o,n))}return a.length>0?s.push(S`<table>
            ${a}
          </table>`):s.push(this.noDataMessage()),s}return[]}getDefaultConfig(){return{display_header:!0,display_description:!0,display_teacher:!0,display_date:!0,display_comment:!0,max_evaluations:null,mapping_evaluations:{}}}static get styles(){return Ke`
      ${super.styles}
      table {
        font-size: 0.9em;
        font-family: Roboto;
        width: 100%;
        outline: 0px solid #393c3d;
        border-collapse: collapse;
      }
      td {
        vertical-align: top;
        padding: 5px 10px 5px 10px;
        text-align: left;
      }
      td.evaluation-color {
        width: 4px;
        padding-top: 11px;
      }
      td.evaluation-color > span {
        display: inline-block;
        width: 4px;
        height: 2rem;
        border-radius: 4px;
        background-color: grey;
      }
      .above-average .evaluation-color > span,
      .above-ratio .evaluation-color > span {
        background-color: green;
      }
      .below-average .evaluation-color > span,
      .below-ratio .evaluation-color > span {
        background-color: orange;
      }
      .evaluation-subject {
        font-weight: bold;
        display: block;
      }
      .evaluation-description {
        display: block;
      }
      .evaluation-teacher {
        display: block;
      }
      .evaluation-date,
      .evaluation-coefficient {
        font-size: 0.9em;
        color: gray;
      }
      .evaluation-comment {
        display: block;
      }
      .evaluation-date + .evaluation-coefficient:before {
        content: " - ";
      }
      .evaluation-detail {
        text-align: right;
      }
      .evaluation-value {
        font-weight: bold;
      }
      .acquisition-icon {
        display: inline-block;
        width: 14px;
        height: 14px;
        border-radius: 50%;
        border: solid 0.02em rgba(0, 0, 0, 0.5);
        margin-left: 4px;
        vertical-align: middle;
        color: white;
        content: "+";
        text-align: center;
        line-height: 14px;
      }
      .acquisition-icon-4 {
        background-color: rgb(0, 176, 80);
      }
      .acquisition-icon-3 {
        background-color: rgb(0, 112, 192);
      }
      .acquisition-icon-2 {
        background-color: rgb(255, 192, 0);
      }
      .acquisition-icon-1 {
        background-color: #f80a0a;
      }
      .acquisition-row {
        display: none;
      }
      input[type="checkbox"] {
        display: none;
      }
      /** FIXME
        .evaluation-row:has(input:checked) .acquisition-icon {
            display:none;
        }
        .evaluation-row:has(input:checked) + .acquisition-row {
            display: table-row;
        }
        */
      .acquisition-row td:nth-child(2) {
        text-align: right;
      }
    `}static getStubConfig(){return{display_header:!0,display_description:!0,display_teacher:!0,display_date:!0,display_comment:!0,max_evaluations:null,mapping_evaluations:{}}}static getConfigElement(){return document.createElement("ecole_directe-evaluations-card-editor")}};customElements.define("ecole_directe-evaluations-card",ae);window.customCards=window.customCards||[];window.customCards.push({type:"ecole_directe-evaluations-card",name:"Carte des \xE9valuations pour Ecole Directe",description:"Affiche les \xE9valuations pour Ecole Directe",documentationURL:"https://github.com/hacf-fr/EcoleDirecteHACards?tab=readme-ov-file#evaluations"});var He=Object.getPrototypeOf(customElements.get("ha-panel-lovelace")),M=He.prototype.html,Qe=He.prototype.css,se=class extends _{getAbsencesRetardsRow(e){let t=M`
      <tr>
        <td class="absence-status">
          <span
            >${e.justifie?M`<ha-icon icon="mdi:check"></ha-icon>`:M`<ha-icon icon="mdi:clock-alert-outline"></ha-icon>`}</span
          >
        </td>
        <td>
          <span
            style="background-color:${e.justifie?"#107c41":"#e73a1f"}"
          ></span>
        </td>
        <td>
          <span class="absence-from">${e.display_date}</span
          ><br /><span class="absence-hours">${e.libelle}</span>
        </td>
        <td>
          <span class="absence-reason">${e.motif}</span>
        </td>
      </tr>
    `;return M`${t}`}initCard(){this.hass.states[this.config.entity].attributes.Absences?(this.items_attribute_key="Absences",this.header_title="Absences de ",this.no_data_message="Aucune absence"):(this.items_attribute_key="Retards",this.header_title="Retards de ",this.no_data_message="Aucun retard")}getCardContent(){if(this.hass.states[this.config.entity]){let t=this.getItems(),i=[],a=[];for(let s=0;s<t.length&&!(this.config.max&&this.config.max<s);s++)a.push(this.getAbsencesRetardsRow(t[s]));return t.length>0?i.push(M`<table>
            ${a}
          </table>`):i.push(this.noDataMessage()),i}}getDefaultConfig(){return{display_header:!0,max:null}}static get styles(){return Qe`
      ${super.styles}
      table {
        clear: both;
        font-size: 0.9em;
        font-family: Roboto;
        width: 100%;
        outline: 0px solid #393c3d;
        border-collapse: collapse;
      }
      tr:nth-child(odd) {
        background-color: rgba(0, 0, 0, 0.1);
      }
      td {
        vertical-align: middle;
        padding: 5px 10px 5px 10px;
        text-align: left;
      }
      tr td:first-child {
        width: 10%;
        text-align: right;
      }
      span.absence-reason {
        font-weight: bold;
        display: block;
      }
      tr td:nth-child(2) {
        width: 4px;
        padding: 5px 0;
      }
      tr td:nth-child(2) > span {
        display: inline-block;
        width: 4px;
        height: 3rem;
        border-radius: 4px;
        background-color: grey;
        margin-top: 4px;
      }
      span.absence-from {
        font-weight: bold;
        padding: 4px;
        border-radius: 4px;
      }
      span.absence-hours {
        font-size: 0.9em;
        padding: 4px;
      }
      table + div {
        border-top: 1px solid white;
      }
    `}static getStubConfig(){return{display_header:!0,max:null}}static getConfigElement(){return document.createElement("ecole_directe-absences-retards-card-editor")}};customElements.define("ecole_directe-absences-retards-card",se);window.customCards=window.customCards||[];window.customCards.push({type:"ecole_directe-absences-retards-card",name:"Carte Absences/Retards pour Ecole Directe",description:"Affiche les absences ou les retards pour Ecole Directe",documentationURL:"https://github.com/hacf-fr/EcoleDirecteHACards?tab=readme-ov-file#absences"});var re=Object.getPrototypeOf(customElements.get("ha-panel-lovelace")),R=re.prototype.html,et=re.prototype.css,ne=class extends re{static get properties(){return{hass:{},_config:{}}}setConfig(e){this._config=e,this.loadEntityPicker()}_valueChanged(e){let t=Object.assign({},this._config);typeof e.target.checked<"u"?t[e.target.configValue]=e.target.checked:t[e.target.configValue]=e.target.value==""?null:e.target.value,this._config=t;let i=new CustomEvent("config-changed",{detail:{config:t},bubbles:!0,composed:!0});this.dispatchEvent(i)}buildSelectField(e,t,i,a,s){let n=[];for(let o=0;o<i.length;o++){let l=i[o];n.push(R`<ha-list-item .value="${l.value}"
          >${l.label}</ha-list-item
        >`)}return R`
      <ha-select
        label="${e}"
        .value=${a||s}
        .configValue=${t}
        @change=${this._valueChanged}
        @closed=${o=>o.stopPropagation()}
      >
        ${n}
      </ha-select>
    `}buildSwitchField(e,t,i,a){return typeof i!="boolean"&&(i=a),R`
      <ha-formfield class="switch-wrapper" .label="${e}">
        <ha-switch
          name="${t}"
          .checked=${i}
          .configValue="${t}"
          @change=${this._valueChanged}
        ></ha-switch>
      </ha-formfield>
    `}buildNumberField(e,t,i,a,s){return R`
      <ha-textfield
        type="number"
        step="${s||1}"
        label="${e}"
        .value=${i||a}
        .configValue=${t}
        @change=${this._valueChanged}
      >
      </ha-textfield>
    `}buildTextField(e,t,i,a){return R`
      <ha-textfield
        label="${e}"
        .value=${i||a}
        .configValue=${t}
        @change=${this._valueChanged}
        @keyup=${this._valueChanged}
      >
      </ha-textfield>
    `}buildEntityPickerField(e,t,i,a){let s=new RegExp("ed_(.*)_"+a);return R`
      <ha-entity-picker
        label="${e}"
        .hass=${this.hass}
        .value=${i||""}
        .configValue=${t}
        .includeDomains="sensor"
        .entityFilter="${n=>s.test(n.entity_id)}"
        @value-changed=${this._valueChanged}
        allow-custom-entity
      ></ha-entity-picker>
    `}async loadEntityPicker(){if(window.customElements.get("ha-entity-picker"))return;await(await(await window.loadCardHelpers()).createCardElement({type:"entities",entities:[]})).constructor.getConfigElement()}static get styles(){return et`
      ha-formfield {
        display: block;
        padding-top: 20px;
        clear: right;
      }
      ha-formfield > ha-switch {
        float: right;
      }
      ha-select,
      ha-textfield {
        clear: right;
        width: 100%;
        padding-top: 15px;
      }
    `}},f=ne;var tt=Object.getPrototypeOf(customElements.get("ha-panel-lovelace")),Oe=tt.prototype.html,oe=class extends f{render(){return!this.hass||!this._config?Oe``:Oe`
      ${this.buildEntityPickerField("Timetable entity","entity",this._config.entity,"emploi_du_temps_(semaine_en_cours|semaine_suivante|semaine_apres_suivante|aujourd_hui|demain|jour_suivant)")}
      ${this.buildSwitchField("Display header","display_header",this._config.display_header,!0)}
      ${this.buildSwitchField("Display classroom","display_classroom",this._config.display_classroom,!0)}
      ${this.buildSwitchField("Display teacher","display_teacher",this._config.display_teacher,!0)}
      ${this.buildSwitchField("Display day hours","display_day_hours",this._config.display_day_hours,!0)}
      ${this.buildSwitchField("Display lunch break","display_lunch_break",this._config.display_lunch_break,!0)}
      ${this.buildSwitchField("Dim ended lessons","dim_ended_lessons",this._config.dim_ended_lessons,!0)}
      ${this.buildSwitchField("Enable slider","enable_slider",this._config.enable_slider,!1)}
      ${this.buildSwitchField("Auto switch to next day (if slider enabled)","switch_to_next_day",this._config.switch_to_next_day,!1)}
      ${this.buildSwitchField("Display free time slots","display_free_time_slots",this._config.display_free_time_slots,!0)}
    `}};customElements.define("ecole_directe-emploi_temps-card-editor",oe);var it=Object.getPrototypeOf(customElements.get("ha-panel-lovelace")),je=it.prototype.html,le=class extends f{render(){return!this.hass||!this._config?je``:je`
      ${this.buildEntityPickerField("Devoir entity","entity",this._config.entity,"devoirs_(semaine_en_cours|semaine_suivante|semaine_apres_suivante|aujourd_hui|demain|jour_suivant)")}
      ${this.buildSwitchField("Display header","display_header",this._config.display_header)}
      ${this.buildSwitchField("Reduce done devoir","reduce_done_devoir",this._config.reduce_done_devoir)}
      ${this.buildSwitchField("Display done devoir","display_done_devoir",this._config.display_done_devoir)}
      ${this.buildSwitchField("Enable slider","enable_slider",this._config.enable_slider,!1)}
    `}};customElements.define("ecole_directe-devoirs-card-editor",le);var at=Object.getPrototypeOf(customElements.get("ha-panel-lovelace")),Me=at.prototype.html,de=class extends f{render(){return!this.hass||!this._config?Me``:Me`
      ${this.buildEntityPickerField("Notes entity","entity",this._config.entity,"notes")}
      ${this.buildSwitchField("Display header","display_header",this._config.display_header)}
      ${this.buildSwitchField("Display date","display_date",this._config.display_date)}
      ${this.buildSwitchField("Display comment","display_comment",this._config.display_comment)}
      ${this.buildSwitchField("Display class average","display_class_average",this._config.display_class_average)}
      ${this.buildSwitchField("Compare with class average","compare_with_class_average",this._config.compare_with_class_average)}
      ${this.buildSelectField("Grade format","grade_format",[{value:"full",label:"Full"},{value:"short",label:"Short"}],this._config.grade_format)}
      ${this.buildSwitchField("Display coefficient","display_coefficient",this._config.display_coefficient)}
      ${this.buildSwitchField("Display class min","display_class_min",this._config.display_class_min)}
      ${this.buildSwitchField("Display class max","display_class_max",this._config.display_class_max)}
      ${this.buildSwitchField("Display new grade notice","display_new_grade_notice",this._config.display_new_grade_notice)}
    `}};customElements.define("ecole_directe-notes-card-editor",de);var st=Object.getPrototypeOf(customElements.get("ha-panel-lovelace")),Pe=st.prototype.html,ce=class extends f{render(){return!this.hass||!this._config?Pe``:Pe`
      ${this.buildEntityPickerField("Evaluations entity","entity",this._config.entity,"evaluations")}
      ${this.buildSwitchField("Display header","display_header",this._config.display_header)}
      ${this.buildSwitchField("Display description","display_description",this._config.display_description)}
      ${this.buildSwitchField("Display teacher","display_teacher",this._config.display_teacher)}
      ${this.buildSwitchField("Display date","display_date",this._config.display_date)}
      ${this.buildSwitchField("Display comment","display_comment",this._config.display_comment)}
      ${this.buildNumberField("Max evaluations","max_evaluations",this._config.max_evaluations)}
    `}};customElements.define("ecole_directe-evaluations-card-editor",ce);var nt=Object.getPrototypeOf(customElements.get("ha-panel-lovelace")),Ne=nt.prototype.html,he=class extends f{render(){return!this.hass||!this._config?Ne``:Ne`
      ${this.buildEntityPickerField("Cpateur moyennes","entity",this._config.entity,"moyenne_generale")}
      ${this.buildSwitchField("Display header","display_header",this._config.display_header)}
      ${this.buildSwitchField("Display class average","display_class_average",this._config.display_class_average)}
      ${this.buildSwitchField("Compare with class average","compare_with_class_average",this._config.compare_with_class_average)}
      ${this.buildTextField("Compare with ratio","compare_with_ratio",this._config.compare_with_ratio,"")}
      ${this.buildSwitchField("Display class min","display_class_min",this._config.display_class_min)}
      ${this.buildSwitchField("Display class max","display_class_max",this._config.display_class_max)}
      ${this.buildSwitchField("Display overall average","display_overall_average",this._config.display_overall_average,!0)}
    `}};customElements.define("ecole_directe-moyennes-card-editor",he);var rt=Object.getPrototypeOf(customElements.get("ha-panel-lovelace")),Be=rt.prototype.html,pe=class extends f{render(){return!this.hass||!this._config?Be``:Be`
      ${this.buildEntityPickerField("Absences/Retards entity","entity",this._config.entity,"(absences|retards)")}
      ${this.buildSwitchField("Display header","display_header",this._config.display_header)}
      ${this.buildNumberField("Max","max",this._config.max)}
    `}};customElements.define("ecole_directe-absences-retards-card-editor",pe);
/*! Bundled license information:

lit-html/lit-html.js:
lit-html/directive.js:
lit-html/directives/unsafe-html.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)
*/
