export const shown = [];
export class ActionFormData {
  constructor() { this.buttons = []; }
  title(t) { this._title = t; return this; }
  body(b) { this._body = b; return this; }
  button(l) { this.buttons.push(l); return this; }
  show(player) { shown.push(this); return new Promise((res) => { this._resolve = res; }); }
}
export class ModalFormData {
  title() { return this; }
  textField() { return this; }
  show() { return new Promise(() => {}); }
}
