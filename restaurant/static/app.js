"use strict";
/*
 * app.js — მენიუსა და კალათის მოქმედებები.
 * HTML აჩვენებს გვერდს, CSS ალამაზებს, ხოლო ეს ფაილი ღილაკებს ამუშავებს.
 * JavaScript უკავშირდება Django-ს; Django კი საჭირო მონაცემებს API-დან ან SQLite-დან იღებს.
 */

// ამ ობიექტში დროებით ვინახავთ იმას, რაც ახლა ეკრანზე გვჭირდება.
const state = {
  products: [],
  categories: [],
  cart: [],
  categoryId: null,
};
const API = "/api";

// პატარა დამხმარე ფუნქციები: თანხის ჩვენება და HTML ელემენტის პოვნა.
const money = value => "$" + Number(value || 0).toFixed(2);
const element = id => document.getElementById(id);

// მიღებულ ტექსტს ისე ვამუშავებთ, რომ HTML-კოდად შემთხვევით არ შესრულდეს.
function escapeHTML(value) {
  const symbols = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };
  return String(value ?? "").replace(/[&<>"']/g, char => symbols[char]);
}

// თუ კერძის სურათის ბმული არასწორია, ვაჩვენებთ სათადარიგო სურათს.
function safeImage(value) {
  try {
    const url = new URL(value);
    if (["http:", "https:"].includes(url.protocol)) return escapeHTML(url.href);
  } catch {
    // არასწორი ბმული — გამოიყენება სათადარიგო სურათი.
  }
  return "/static/food-placeholder.svg";
}

// Django-ის CSRF cookie გვჭირდება კალათის შეცვლის მოთხოვნებისათვის.
function getCookie(name) {
  const pair = document.cookie.split("; ").find(item => item.startsWith(name + "="));
  return pair ? decodeURIComponent(pair.slice(name.length + 1)) : "";
}

// აქ გადის ყველა მოთხოვნა Django-ს /api მისამართებზე (GET, POST, PUT, DELETE).
async function request(path, options = {}) {
  const method = (options.method || "GET").toUpperCase();
  const headers = { Accept: "application/json" };

  // როცა მონაცემებს ვაგზავნით, ვუთითებთ JSON ფორმატსა და CSRF დაცვას.
  if (options.body) headers["Content-Type"] = "application/json";
  if (!["GET", "HEAD", "OPTIONS"].includes(method)) {
    headers["X-CSRFToken"] = getCookie("csrftoken");
  }

  const response = await fetch(API + path, {
    ...options,
    credentials: "same-origin",
    headers: { ...headers, ...(options.headers || {}) },
  });
  const text = await response.text();
  let data;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = { error: "სერვერის პასუხი არასწორია" };
  }
  if (!response.ok) throw new Error(data?.error || `API შეცდომა (${response.status})`);
  return data;
}

// ეკრანის ქვედა კუთხეში ვაჩვენებთ პატარა შეტყობინებას.
let toastTimer;
function toast(message, isError = false) {
  const box = element("toast");
  if (!box) return;
  box.textContent = message;
  box.className = "toast show" + (isError ? " error" : "");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { box.className = "toast"; }, 3200);
}

// თუ API პასუხს ვერ აბრუნებს, ვაჩვენებთ შეცდომას და ხელახალი ცდის ღილაკს.
function renderError(target, error, retry) {
  target.innerHTML = `
    <div class="loading-panel error-panel">
      <strong>მონაცემები ვერ ჩაიტვირთა</strong>
      <p>${escapeHTML(error.message || String(error))}</p>
      <button type="button" class="retry-button">თავიდან ცდა</button>
    </div>`;
  target.querySelector(".retry-button").addEventListener("click", retry);
}

// SQLite-ში შენახული კალათა მოდის Django-დან; ზედა ნაწილში რაოდენობას ვაახლებთ.
async function loadCartCount() {
  const cart = await request("/Baskets/GetAll");
  if (!Array.isArray(cart)) throw new Error("კალათის მონაცემები არასწორია");
  state.cart = cart;
  const totalCount = cart.reduce((sum, item) => sum + Number(item.quantity), 0);
  document.querySelectorAll("[data-cart-count]").forEach(node => {
    node.textContent = String(totalCount);
  });
}

// კატეგორიის ID-ის ნაცვლად მომხმარებელს ტექსტურ სახელს ვაჩვენებთ.
function categoryName(id) {
  return state.categories.find(item => Number(item.id) === Number(id))?.name || "კერძი";
}

// პროდუქტების ბარათებში სურათის HTML-ს ვამზადებთ.
function productImage(product) {
  return `<img class="product-image" src="${safeImage(product.image)}"
    alt="${escapeHTML(product.name)}" loading="lazy"
    onerror="this.onerror=null;this.src='/static/food-placeholder.svg'">`;
}

// პროდუქტის მახასიათებლებს ვაჩვენებთ პატარა ნიშნებით.
function productTags(product) {
  return `
    <span class="tag spicy">🌶 ${Number(product.spiciness ?? 0)}/4</span>
    <span class="tag ${product.nuts ? "" : "positive"}">${product.nuts ? "ნიგვზიანი" : "ნიგვზის გარეშე"}</span>
    <span class="tag ${product.vegeterian ? "positive" : ""}">${product.vegeterian ? "ვეგეტარიანული" : "არავეგეტარიანული"}</span>`;
}

// მარცხნივ ვხატავთ კატეგორიების ღილაკებს და მათზე დაჭერისას ვფილტრავთ.
function renderCategories() {
  const list = element("categories");
  const allButton = `
    <button type="button" class="category-item ${state.categoryId === null ? "active" : ""}"
      data-category="">ყველა კატეგორია <span class="category-arrow">→</span></button>`;
  const otherButtons = state.categories.map(category => `
    <button type="button" class="category-item ${state.categoryId === Number(category.id) ? "active" : ""}"
      data-category="${Number(category.id)}">${escapeHTML(category.name)}
      <span class="category-arrow">→</span></button>`).join("");
  list.innerHTML = allButton + otherButtons;

  // თითოეული კატეგორიის ღილაკს ვუკავშირებთ ფილტრის განახლებას.
  list.querySelectorAll("[data-category]").forEach(button => {
    button.addEventListener("click", () => {
      state.categoryId = button.dataset.category ? Number(button.dataset.category) : null;
      renderCategories();
      loadProducts();
    });
  });
}

// API-დან მიღებული პროდუქტებით მენიუს ბარათებს ვქმნით.
function renderProducts() {
  const grid = element("products");
  element("results-count").textContent = `(${state.products.length})`;
  if (!state.products.length) {
    grid.innerHTML = '<div class="empty-state"><h3>კერძები ვერ მოიძებნა</h3><p>სცადე სხვა ფილტრის არჩევა.</p></div>';
    return;
  }

  // თითოეულ პროდუქტს აქვს ფოტო, ფასი, მახასიათებლები და დამატების ღილაკი.
  grid.innerHTML = state.products.map(product => `
    <article class="product-card">
      <div class="product-image-wrap">
        ${productImage(product)}
        <span class="product-category">${escapeHTML(categoryName(product.categoryId))}</span>
      </div>
      <div class="product-body">
        <h3 class="product-title">${escapeHTML(product.name)}</h3>
        <div class="product-tags">${productTags(product)}</div>
        <div class="product-bottom">
          <span class="product-price">${money(product.price)}</span>
          <button class="add-btn" type="button" data-add="${Number(product.id)}"
            aria-label="${escapeHTML(product.name)} კალათაში დამატება">+</button>
        </div>
      </div>
    </article>`).join("");

  grid.querySelectorAll("[data-add]").forEach(button => {
    button.addEventListener("click", () => addProduct(Number(button.dataset.add), button));
  });
}

// ფილტრების არჩევის შემდეგ Django-ს ვთხოვთ შესაბამის კერძებს.
// ნომერი გვიცავს: თუ მომხმარებელი სწრაფად ცვლის ფილტრებს, მხოლოდ ბოლო პასუხს ვაჩვენებთ.
let latestFilterRequest = 0;
async function loadProducts() {
  const requestNo = ++latestFilterRequest;
  const params = new URLSearchParams();
  if (state.categoryId !== null) params.set("categoryId", String(state.categoryId));
  for (const key of ["spiciness", "nuts", "vegeterian"]) {
    const value = element(key).value;
    if (value !== "") params.set(key, value);
  }

  const endpoint = params.size ? "/Products/GetFiltered?" + params.toString() : "/Products/GetAll";
  element("products").innerHTML = '<div class="loading-panel">კერძები იტვირთება...</div>';
  try {
    const products = await request(endpoint);
    if (requestNo !== latestFilterRequest) return;
    if (!Array.isArray(products)) throw new Error("API-დან არასწორი მონაცემები მივიღეთ");
    state.products = products;
    renderProducts();
  } catch (error) {
    if (requestNo === latestFilterRequest) renderError(element("products"), error, loadProducts);
  }
}

// მენიუს "+" ღილაკით შესულ მომხმარებელს SQLite კალათაში ერთი კერძი ემატება.
async function addProduct(id, button) {
  if (document.body.dataset.authenticated !== "true") {
    window.location.assign("/login/?next=/");
    return;
  }
  const product = state.products.find(item => Number(item.id) === id);
  if (!product || button.disabled) return;
  button.disabled = true;
  try {
    await request("/Baskets/AddToBasket", {
      method: "POST",
      body: JSON.stringify({ productId: id, quantity: 1 }),
    });
    toast("კერძი დაემატა კალათაში ✓");
    try {
      await loadCartCount();
    } catch {
      toast("კერძი დაემატა, მაგრამ კალათის რაოდენობა ვერ განახლდა", true);
    }
  } catch (error) {
    toast(error.message, true);
  } finally {
    button.disabled = false;
  }
}

// მენიუს გახსნისას ვტვირთავთ კატეგორიებს, კერძებსა და კალათის რაოდენობას.
async function initMenu() {
  element("apply-filters").addEventListener("click", loadProducts);
  element("clear-filters").addEventListener("click", () => {
    state.categoryId = null;
    for (const key of ["spiciness", "nuts", "vegeterian"]) element(key).value = "";
    renderCategories();
    loadProducts();
  });
  try {
    state.categories = await request("/Categories/GetAll");
    renderCategories();
    await loadProducts();
  } catch (error) {
    renderError(element("products"), error, initMenu);
    element("categories").innerHTML = '<span class="placeholder-line">კატეგორიები მიუწვდომელია</span>';
  }
  if (document.body.dataset.authenticated === "true") {
    loadCartCount().catch(() => {});
  }
}

// კალათის გვერდზე თითოეული კერძის რაოდენობას და საერთო ფასს ვთვლით.
function renderCart() {
  const rows = state.cart;
  const section = element("cart-items");
  const count = rows.reduce((sum, row) => sum + Number(row.quantity), 0);
  const total = rows.reduce((sum, row) => sum + Number(row.price) * Number(row.quantity), 0);
  element("summary-quantity").textContent = String(count);
  element("subtotal").textContent = money(total);
  element("total").textContent = money(total);

  // თუ კალათა ცარიელია, კერძების ნაცვლად შესაბამის ტექსტს ვაჩვენებთ.
  if (!rows.length) {
    section.innerHTML = `
      <div class="empty-state">
        <span class="empty-state-symbol">▤</span>
        <h3>კალათა ცარიელია</h3>
        <p>მენიუდან დაამატე შენთვის სასურველი კერძები.</p>
        <a href="/" class="button button-accent">მენიუს ნახვა →</a>
      </div>`;
    return;
  }

  // ყოველი კერძისთვის ვხატავთ რაოდენობის ღილაკებსა და წაშლის ღილაკს.
  section.innerHTML = rows.map(row => `
    <article class="cart-item" data-item="${Number(row.productId)}">
      <img class="cart-item-image" src="${safeImage(row.product.image)}"
        alt="${escapeHTML(row.product.name)}"
        onerror="this.onerror=null;this.src='/static/food-placeholder.svg'">
      <div class="cart-item-description">
        <span class="mini-category">${escapeHTML(categoryName(row.product.categoryId))}</span>
        <h3>${escapeHTML(row.product.name)}</h3>
        <div class="cart-item-meta">${productTags(row.product)}</div>
        <span class="muted">ერთეულის ფასი: ${money(row.price)}</span>
      </div>
      <div class="cart-item-controls">
        <span class="cart-item-price">${money(row.price * row.quantity)}</span>
        <div class="quantity-control">
          <button type="button" class="qty-button" data-change="-1" data-product-id="${row.productId}" aria-label="რაოდენობის შემცირება">−</button>
          <span class="qty-number">${row.quantity}</span>
          <button type="button" class="qty-button" data-change="1" data-product-id="${row.productId}" aria-label="რაოდენობის გაზრდა">+</button>
        </div>
        <button type="button" class="remove-button" data-remove="${row.productId}">✕ წაშლა</button>
      </div>
    </article>`).join("");

  // ღილაკებზე დაჭერა შესაბამის ფუნქციებს იძახებს.
  section.querySelectorAll("[data-change]").forEach(button => {
    button.addEventListener("click", () => {
      changeQuantity(Number(button.dataset.productId), Number(button.dataset.change));
    });
  });
  section.querySelectorAll("[data-remove]").forEach(button => {
    button.addEventListener("click", () => removeProduct(Number(button.dataset.remove)));
  });
}

// ცვლილების დასრულებამდე სხვა ღილაკებს დროებით ვთიშავთ.
let basketBusy = false;
function disableCartButtons() {
  element("cart-items").querySelectorAll("button").forEach(button => { button.disabled = true; });
}

// პლუსი/მინუსი ცვლის რაოდენობას; ნულამდე შემცირებისას კერძი იშლება.
async function changeQuantity(id, delta) {
  if (basketBusy) return;
  const row = state.cart.find(item => Number(item.productId) === id);
  if (!row) return;
  const quantity = Number(row.quantity) + delta;
  if (quantity <= 0) return removeProduct(id);
  basketBusy = true;
  disableCartButtons();
  try {
    await request("/Baskets/UpdateBasket", {
      method: "PUT",
      body: JSON.stringify({ productId: id, quantity }),
    });
    await refreshCart();
  } catch (error) {
    toast(error.message, true);
    renderCart();
  } finally {
    basketBusy = false;
  }
}

// „წაშლა“ ღილაკი Django-ს სთხოვს კალათიდან ამ კერძის წაშლას.
async function removeProduct(id) {
  if (basketBusy) return;
  basketBusy = true;
  disableCartButtons();
  try {
    await request("/Baskets/DeleteProduct/" + id, { method: "DELETE" });
    await refreshCart();
    toast("კერძი წაიშალა კალათიდან");
  } catch (error) {
    toast(error.message, true);
    renderCart();
  } finally {
    basketBusy = false;
  }
}

// ყოველი ცვლილების შემდეგ SQLite-დან ახლიდან ვკითხულობთ კალათას და ვხატავთ.
async function refreshCart() {
  await loadCartCount();
  renderCart();
}

// კალათის გვერდს კატეგორიების სახელები და მომხმარებლის პირადი კალათა სჭირდება.
// პროდუქტების სრული სიის ხელახლა ჩამოტვირთვა საჭირო არ არის: მონაცემები კალათაშივეა.
async function initCart() {
  try {
    state.categories = await request("/Categories/GetAll");
    await refreshCart();
  } catch (error) {
    renderError(element("cart-items"), error, initCart);
  }
}

// გვერდის ჩატვირთვისას საჭირო ფუნქციას ვუშვებთ: მენიუს ან კალათისათვის.
document.addEventListener("DOMContentLoaded", () => {
  if (document.body.dataset.page === "menu") initMenu();
  if (document.body.dataset.page === "cart") initCart();
});
