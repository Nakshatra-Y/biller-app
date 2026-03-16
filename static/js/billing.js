function formatCurrency(num) {
  return "₹" + num.toFixed(2);
}

document.addEventListener("DOMContentLoaded", () => {
  const productGrid = document.getElementById("productGrid");
  const categoryList = document.getElementById("categoryList");
  const categoryCards = categoryList ? categoryList.querySelectorAll(".category-card:not(#addCategoryCard)") : [];
  const addCategoryCard = document.getElementById("addCategoryCard");
  const addTableCard = document.getElementById("addTableCard");
  const tableGrid = document.getElementById("tableGrid");
  const billItemsBody = document.getElementById("billItemsBody");
  const billTotalEl = document.getElementById("billTotal");
  const billSubtotalEl = document.getElementById("billSubtotal");
  const gstInput = document.getElementById("gstInput");
  const saveBillBtn = document.getElementById("saveBillBtn");
  const tableCards = document.querySelectorAll(".table-card");
  let selectedTable = null;
  const productSearch = document.getElementById("productSearch");
  const printBillBtn = document.getElementById("printBillBtn");

  const bill = {
    items: {},
    get itemsArray() {
      return Object.values(this.items);
    },
    get subtotal() {
      return this.itemsArray.reduce((acc, item) => acc + item.price * item.quantity, 0);
    },
    get total() {
      const gstRate = parseFloat(gstInput ? gstInput.value || "0" : "0");
      const base = this.subtotal;
      if (!gstRate || Number.isNaN(gstRate)) return base;
      return base + (base * gstRate) / 100;
    },
  };

  function statusLabel(s) {
    if (s === "available") return "Empty";
    if (s === "pending") return "Pending";
    return "Occupied";
  }

  if (tableCards.length) {
    tableCards.forEach((card) => {
      if (card.id === "addTableCard") return;
      card.addEventListener("click", (e) => {
        if (e.target.closest(".table-card-edit")) return;
      
        const status = card.dataset.status || "available";
      
        // Only allow empty tables to be selected
        if (status !== "available") {
          if (window.showNotification) {
            showNotification("Please click on an empty table.", "error");
          }
          return;
        }
      
        tableCards.forEach((c) => c.classList.remove("active"));
        card.classList.add("active");
        selectedTable = card.dataset.table;
      });
    });
  }

  const editTableModal = document.getElementById("editTableModal");
  const editTableInput = document.getElementById("editTableInput");
  const editTableSave = document.getElementById("editTableSave");
  const editTableCancel = document.getElementById("editTableCancel");
  let editingTableId = null;
  let editingTableCard = null;

  if (tableGrid) {
    tableGrid.querySelectorAll(".table-card[data-table-id]").forEach((card) => {
      const editBtn = card.querySelector(".table-card-edit");
      if (!editBtn) return;
      editBtn.addEventListener("click", (e) => {
        e.preventDefault();
        e.stopPropagation();
        editingTableId = card.getAttribute("data-table-id");
        editingTableCard = card;
        if (editTableInput) editTableInput.value = card.dataset.table || "";
        if (editTableModal) editTableModal.classList.remove("hidden");
      });
    });
  }

  if (editTableCancel && editTableModal) {
    editTableCancel.addEventListener("click", () => {
      editTableModal.classList.add("hidden");
      editingTableId = null;
      editingTableCard = null;
    });
  }
  if (editTableModal) {
    editTableModal.addEventListener("click", (e) => {
      if (e.target.classList.contains("modal-backdrop")) editTableModal.classList.add("hidden");
    });
  }
  if (editTableSave && editTableInput) {
    editTableSave.addEventListener("click", async () => {
      if (!editingTableId) return;
      const num = String(editTableInput.value).trim();
      if (!num) {
        if (window.showNotification) showNotification("Enter a table number.", "error");
        return;
      }
      try {
        const res = await fetch("/api/tables/" + editingTableId, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ table_number: num }),
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
          if (window.showNotification) showNotification(data.error || "Failed to update table", "error");
          return;
        }
        if (editingTableCard) {
          const numEl = editingTableCard.querySelector(".table-number");
          if (numEl) numEl.textContent = "Table " + data.table_number;
          editingTableCard.dataset.table = data.table_number;
        }
        editTableModal.classList.add("hidden");
        editingTableId = null;
        editingTableCard = null;
        if (window.showNotification) showNotification("Table updated.", "success");
      } catch (err) {
        if (window.showNotification) showNotification("Network error.", "error");
      }
    });
  }

  if (addTableCard) {
    addTableCard.addEventListener("click", () => {
      const addTableModal = document.getElementById("addTableModal");
      const addTableInput = document.getElementById("addTableInput");
      if (addTableModal) addTableModal.classList.remove("hidden");
      if (addTableInput) addTableInput.value = "";
    });
  }
  const addTableModalEl = document.getElementById("addTableModal");
  const addTableInputEl = document.getElementById("addTableInput");
  const addTableSubmit = document.getElementById("addTableSubmit");
  const addTableCancel = document.getElementById("addTableCancel");
  if (addTableCancel && addTableModalEl) {
    addTableCancel.addEventListener("click", () => addTableModalEl.classList.add("hidden"));
  }
  if (addTableModalEl) {
    addTableModalEl.addEventListener("click", (e) => {
      if (e.target.classList.contains("modal-backdrop")) addTableModalEl.classList.add("hidden");
    });
  }
  if (addTableSubmit && addTableInputEl) {
    addTableSubmit.addEventListener("click", async () => {
      const num = String(addTableInputEl.value).trim();
      if (!num) {
        if (window.showNotification) showNotification("Enter a table number.", "error");
        return;
      }
      try {
        const res = await fetch("/api/tables", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ table_number: num }),
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
          if (window.showNotification) showNotification(data.error || "Failed to add table", "error");
          return;
        }
        if (window.showNotification) showNotification("Table added.", "success");
        addTableModalEl.classList.add("hidden");
        location.reload();
      } catch (err) {
        if (window.showNotification) showNotification("Network error.", "error");
      }
    });
  }

  if (tableGrid) {
    function pollTableStatus() {
      fetch("/api/table-status")
        .then((r) => (r.ok ? r.json() : null))
        .then((data) => {
          if (!data || !data.tables) return;
          data.tables.forEach((t) => {
            const card = tableGrid.querySelector('[data-table-id="' + t.id + '"]');
            if (!card) return;
            const status = t.status || "available";
            const isAvailable = status === "available";
            card.classList.remove("table-available", "table-pending", "table-occupied");
            card.classList.add(isAvailable ? "table-available" : "table-occupied");
            card.dataset.status = status;
            if (t.pending_bill_id) card.dataset.pendingBillId = t.pending_bill_id;
            else delete card.dataset.pendingBillId;
            const statusEl = card.querySelector(".table-status");
            if (statusEl) statusEl.textContent = statusLabel(status);
          });
        })
        .catch(() => {});
    }
    pollTableStatus();
    setInterval(pollTableStatus, 3000);
  }

  if (categoryCards.length) {
    categoryCards.forEach((btn) => {
      btn.addEventListener("click", () => {
        categoryCards.forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        const cat = btn.dataset.category;
        if (!productGrid) return;
        productGrid.querySelectorAll(".product-card").forEach((card) => {
          if (cat === "all" || card.dataset.category === cat) {
            card.style.display = "";
          } else {
            card.style.display = "none";
          }
        });
      });
    });
  }

  if (addCategoryCard) {
    addCategoryCard.addEventListener("click", () => {
      const addCategoryModal = document.getElementById("addCategoryModal");
      const addCategoryInput = document.getElementById("addCategoryInput");
      if (addCategoryModal) addCategoryModal.classList.remove("hidden");
      if (addCategoryInput) addCategoryInput.value = "";
    });
  }
  const addCategoryModalEl = document.getElementById("addCategoryModal");
  const addCategoryInputEl = document.getElementById("addCategoryInput");
  const addCategorySubmit = document.getElementById("addCategorySubmit");
  const addCategoryCancel = document.getElementById("addCategoryCancel");
  if (addCategoryCancel && addCategoryModalEl) {
    addCategoryCancel.addEventListener("click", () => addCategoryModalEl.classList.add("hidden"));
  }
  if (addCategoryModalEl) {
    addCategoryModalEl.addEventListener("click", (e) => {
      if (e.target.classList.contains("modal-backdrop")) addCategoryModalEl.classList.add("hidden");
    });
  }
  if (addCategorySubmit && addCategoryInputEl) {
    addCategorySubmit.addEventListener("click", async () => {
      const name = String(addCategoryInputEl.value).trim();
      if (!name) {
        if (window.showNotification) showNotification("Enter a category name.", "error");
        return;
      }
      try {
        const res = await fetch("/menu/category", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ name: name }),
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
          if (window.showNotification) showNotification(data.error || "Failed to add category", "error");
          return;
        }
        if (window.showNotification) showNotification("Category added.", "success");
        addCategoryModalEl.classList.add("hidden");
        location.reload();
      } catch (err) {
        if (window.showNotification) showNotification("Network error.", "error");
      }
    });
  }

  function renderBill() {
    if (!billItemsBody) return;
    billItemsBody.innerHTML = "";
    bill.itemsArray.forEach((item) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${item.name}</td>
        <td>
          <button class="btn btn-small btn-secondary js-qty-minus" data-id="${item.id}">-</button>
          <span style="margin:0 4px;">${item.quantity}</span>
          <button class="btn btn-small btn-secondary js-qty-plus" data-id="${item.id}">+</button>
        </td>
        <td>${formatCurrency(item.price * item.quantity)}</td>
        <td><button class="btn btn-small btn-danger js-remove-item" data-id="${item.id}">×</button></td>
      `;
      billItemsBody.appendChild(tr);
    });
    if (billSubtotalEl) billSubtotalEl.textContent = formatCurrency(bill.subtotal);
    if (billTotalEl) billTotalEl.textContent = formatCurrency(bill.total);
  }

  if (gstInput) {
    gstInput.addEventListener("input", () => {
      renderBill();
    });
  }

  if (productGrid) {
    productGrid.addEventListener("click", (e) => {
      const card = e.target.closest(".product-card");
      if (!card) return;
      const id = card.dataset.id;
      const name = card.dataset.name;
      const price = parseFloat(card.dataset.price);
      if (!bill.items[id]) {
        bill.items[id] = { id, name, price, quantity: 1 };
      } else {
        bill.items[id].quantity += 1;
      }
      renderBill();
    });
  }

  if (billItemsBody) {
    billItemsBody.addEventListener("click", (e) => {
      const minus = e.target.closest(".js-qty-minus");
      const plus = e.target.closest(".js-qty-plus");
      const remove = e.target.closest(".js-remove-item");
      if (!minus && !plus && !remove) return;
      const id = (minus || plus || remove).dataset.id;
      const item = bill.items[id];
      if (!item) return;
      if (remove) {
        delete bill.items[id];
      } else if (minus) {
        item.quantity -= 1;
        if (item.quantity <= 0) delete bill.items[id];
      } else if (plus) {
        item.quantity += 1;
      }
      renderBill();
    });
  }


  if (productSearch && productGrid) {
    productSearch.addEventListener("input", () => {
      const query = productSearch.value.toLowerCase();
      productGrid.querySelectorAll(".product-card").forEach((card) => {
        const name = (card.dataset.name || "").toLowerCase();
        const matches = name.includes(query);
        card.style.display = matches ? "" : "none";
      });
    });
  }

  if (saveBillBtn) {
    saveBillBtn.addEventListener("click", async () => {
      if (!selectedTable) {
        if (window.showNotification) showNotification("Please select a table first.", "error");
        return;
      }
      if (!bill.itemsArray.length) {
        if (window.showNotification) showNotification("Please add at least one item.", "error");
        return;
      }
      const payload = {
        table_no: selectedTable,
        items: bill.itemsArray.map((i) => ({
          product_name: i.name,
          price: i.price,
          quantity: i.quantity,
        })),
        gst_rate: parseFloat(gstInput ? gstInput.value || "0" : "0"),
      };
      try {
        const res = await fetch("/bills", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(payload),
        });
        if (!res.ok) {
          const data = await res.json().catch(() => ({}));
          if (window.showNotification) showNotification("Failed to save bill: " + (data.error || res.statusText), "error");
          return;
        }
        Object.keys(bill.items).forEach((k) => delete bill.items[k]);
        renderBill();
        if (window.showNotification) showNotification("Bill generated.", "success");
      } catch (err) {
        console.error(err);
        if (window.showNotification) showNotification("Network error while saving bill.", "error");
      }
    });
  }

  if (printBillBtn) {
    printBillBtn.addEventListener("click", () => {
      window.print();
    });
  }

  document.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      if (saveBillBtn) {
        e.preventDefault();
        saveBillBtn.click();
      }
    }
    if (e.key === "Backspace") {
      const ids = Object.keys(bill.items);
      if (!ids.length) return;
      const lastId = ids[ids.length - 1];
      delete bill.items[lastId];
      renderBill();
    }
  });

  const billModal = document.getElementById("billModal");
  const billModalBody = document.getElementById("billModalBody");
  const billModalEditable = document.getElementById("billModalEditable");
  const billModalViewOnly = document.getElementById("billModalViewOnly");
  const billModalViewContent = document.getElementById("billModalViewContent");
  const billModalItemsBody = document.getElementById("billModalItemsBody");
  const billModalTotal = document.getElementById("billModalTotal");
  const billModalSave = document.getElementById("billModalSave");
  const billModalComplete = document.getElementById("billModalComplete");
  const billModalPrint = document.getElementById("billModalPrint");
  const closeBillModal = document.getElementById("closeBillModal");

  let currentBillId = null;
  let modalEditableItems = [];
  let modalIsPending = false;

  function openModal() {
    if (billModal) billModal.classList.remove("hidden");
  }

  function closeModal() {
    if (billModal) billModal.classList.add("hidden");
    currentBillId = null;
  }

  function modalItemsTotal() {
    return modalEditableItems.reduce((s, i) => s + i.price * i.quantity, 0);
  }

  function renderModalItems() {
    if (!billModalItemsBody) return;
    billModalItemsBody.innerHTML = "";
    modalEditableItems.forEach((item, idx) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${item.product_name}</td>
        <td>
          <button type="button" class="btn btn-small btn-secondary js-modal-qty-minus" data-idx="${idx}">−</button>
          <span style="margin:0 6px;">${item.quantity}</span>
          <button type="button" class="btn btn-small btn-secondary js-modal-qty-plus" data-idx="${idx}">+</button>
        </td>
        <td>${formatCurrency(item.price * item.quantity)}</td>
        <td><button type="button" class="btn btn-small btn-danger js-modal-remove" data-idx="${idx}">×</button></td>
      `;
      billModalItemsBody.appendChild(tr);
    });
    if (billModalTotal) billModalTotal.textContent = formatCurrency(modalItemsTotal());
  }

  if (billModalItemsBody) {
    billModalItemsBody.addEventListener("click", (e) => {
      const minus = e.target.closest(".js-modal-qty-minus");
      const plus = e.target.closest(".js-modal-qty-plus");
      const remove = e.target.closest(".js-modal-remove");
      if (!minus && !plus && !remove) return;
      const idx = parseInt((minus || plus || remove).dataset.idx, 10);
      const item = modalEditableItems[idx];
      if (!item) return;
      if (remove) {
        modalEditableItems.splice(idx, 1);
      } else if (minus) {
        item.quantity -= 1;
        if (item.quantity <= 0) modalEditableItems.splice(idx, 1);
      } else {
        item.quantity += 1;
      }
      renderModalItems();
    });
  }

  if (closeBillModal && billModal) {
    closeBillModal.addEventListener("click", closeModal);
    billModal.addEventListener("click", (e) => {
      if (e.target.classList.contains("modal-backdrop")) closeModal();
    });
  }

  if (billModalSave) {
    billModalSave.addEventListener("click", async () => {
      if (!currentBillId || !modalEditableItems.length) {
        if (window.showNotification) showNotification("Add at least one item.", "error");
        else if (window.showToast) showToast("Add at least one item.", "error");
        return;
      }
      try {
        const res = await fetch(`/bills/${currentBillId}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            items: modalEditableItems.map((i) => ({
              product_name: i.product_name,
              price: i.price,
              quantity: i.quantity,
            })),
            gst_rate: 0,
          }),
        });
        const d = await res.json().catch(() => ({}));
        if (!res.ok) {
          if (window.showNotification) showNotification(d.error || "Failed to save bill", "error");
          return;
        }
        if (window.showNotification) showNotification("Bill updated.", "success");
        closeModal();
        location.reload();
      } catch (err) {
        if (window.showNotification) showNotification("Network error.", "error");
      }
    });
  }

  if (billModalComplete) {
    billModalComplete.addEventListener("click", async () => {
      if (!currentBillId) return;
      try {
        const res = await fetch(`/bills/${currentBillId}/complete`, { method: "PUT" });
        if (!res.ok) {
          if (window.showNotification) showNotification("Failed to complete bill.", "error");
          return;
        }
        if (window.showNotification) showNotification("Successfully completed.", "success");
        closeModal();
        pollTableStatus();
      } catch (err) {
        if (window.showNotification) showNotification("Network error.", "error");
      }
    });
  }

  if (billModalPrint) {
    billModalPrint.addEventListener("click", () => {
      if (currentBillId) window.open(`/bills/${currentBillId}/receipt`, "_blank", "width=400,height=600");
    });
  }

  function openEditableModal(data) {
    currentBillId = data.id;
    modalEditableItems = data.items.map((i) => ({
      product_name: i.product_name,
      price: i.price,
      quantity: i.quantity,
    }));
    const title = document.getElementById("billModalTitle");
    if (title) title.textContent = `Bill #${data.id} – Table ${data.table_no}`;
    if (billModalBody) billModalBody.classList.add("hidden");
    if (billModalViewOnly) billModalViewOnly.classList.add("hidden");
    if (billModalEditable) {
      billModalEditable.classList.remove("hidden");
      renderModalItems();
    }
    if (billModalComplete) billModalComplete.style.display = modalIsPending ? "" : "none";
    filterModalProductOptions();
    openModal();
  }

  const modalAddCategory = document.getElementById("modalAddCategory");
  const modalAddProduct = document.getElementById("modalAddProduct");
  const modalAddItemBtn = document.getElementById("modalAddItemBtn");

  function filterModalProductOptions() {
    if (!modalAddProduct) return;
    const cat = modalAddCategory ? modalAddCategory.value : "";
    const options = modalAddProduct.querySelectorAll("option");
    options.forEach((opt) => {
      if (opt.value === "") {
        opt.hidden = false;
        return;
      }
      if (cat === "" || cat === "all" || opt.dataset.category === cat) {
        opt.hidden = false;
      } else {
        opt.hidden = true;
      }
    });
    modalAddProduct.value = "";
  }

  if (modalAddCategory) {
    modalAddCategory.addEventListener("change", filterModalProductOptions);
  }

  if (modalAddItemBtn && modalAddProduct) {
    modalAddItemBtn.addEventListener("click", () => {
      const opt = modalAddProduct.options[modalAddProduct.selectedIndex];
      if (!opt || !opt.value) {
        if (window.showNotification) showNotification("Select a product.", "error");
        return;
      }
      const name = opt.dataset.name || opt.textContent.split(" – ")[0] || "";
      const price = parseFloat(opt.dataset.price || "0");
      if (!name || isNaN(price)) return;
      const existing = modalEditableItems.find((i) => i.product_name === name && i.price === price);
      if (existing) existing.quantity += 1;
      else modalEditableItems.push({ product_name: name, price: price, quantity: 1 });
      renderModalItems();
      modalAddProduct.value = "";
    });
  }

  function openViewOnlyModal(data) {
    currentBillId = data.id;
    const title = document.getElementById("billModalTitle");
    if (title) title.textContent = `Bill #${data.id} – Table ${data.table_no}`;
    if (billModalBody) billModalBody.classList.add("hidden");
    if (billModalEditable) billModalEditable.classList.add("hidden");
    if (billModalViewOnly) {
      billModalViewOnly.classList.remove("hidden");
      if (billModalViewContent) {
        billModalViewContent.innerHTML = `
          <table class="data-table">
            <thead><tr><th>Item</th><th>Qty</th><th>Subtotal</th></tr></thead>
            <tbody>
              ${data.items.map((i) => `<tr><td>${i.product_name}</td><td>${i.quantity}</td><td>${formatCurrency(i.price * i.quantity)}</td></tr>`).join("")}
            </tbody>
          </table>
          <p style="margin-top:8px;"><strong>Total:</strong> ${formatCurrency(data.total)}</p>
        `;
      }
    }
    openModal();
  }

  document.querySelectorAll(".js-view-bill").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const id = btn.dataset.id;
      try {
        const res = await fetch(`/bills/${id}`);
        if (!res.ok) return;
        const data = await res.json();
        modalIsPending = true;
        openEditableModal(data);
      } catch (e) {
        console.error(e);
      }
    });
  });

  document.querySelectorAll(".js-complete-bill").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const id = btn.dataset.id;
      try {
        const res = await fetch(`/bills/${id}/complete`, { method: "PUT" });
        if (!res.ok) {
          if (window.showNotification) showNotification("Failed to complete bill.", "error");
          else if (window.showToast) showToast("Failed to complete bill.", "error");
          return;
        }
        if (window.showNotification) showNotification("Successfully completed.", "success");
        else if (window.showToast) showToast("Bill completed.", "success");
        if (typeof pollTableStatus === "function") {
          pollTableStatus();
        }
      } catch (e) {
        if (window.showNotification) showNotification("Network error.", "error");
        else if (window.showToast) showToast("Network error.", "error");
      }
    });
  });

  document.querySelectorAll(".js-print-receipt").forEach((btn) => {
    btn.addEventListener("click", () => {
      const id = btn.dataset.id;
      window.open(`/bills/${id}/receipt`, "_blank", "width=400,height=600");
    });
  });

  document.querySelectorAll(".js-edit-bill-completed").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const id = btn.dataset.id;
      try {
        const res = await fetch(`/bills/${id}`);
        if (!res.ok) return;
        const data = await res.json();
        modalIsPending = true;
        openEditableModal(data);
      } catch (e) {
        console.error(e);
      }
    });
  });
});

