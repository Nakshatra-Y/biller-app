document.addEventListener("DOMContentLoaded", () => {
  const categoryForm = document.getElementById("categoryForm");
  const productForm = document.getElementById("productForm");
  const categoryListAdmin = document.getElementById("categoryListAdmin");
  const productTableBody = document.getElementById("productTableBody");

  if (categoryForm) {
    categoryForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const formData = new FormData(categoryForm);
      const payload = { name: formData.get("name") };
      try {
        const res = await fetch("/menu/category", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
          if (window.showToast) showToast(data.error || "Failed to create category", "error");
          return;
        }
        if (categoryListAdmin) {
          const li = document.createElement("li");
          li.className = "pill";
          li.dataset.id = data.id;
          li.innerHTML = `
            <span class="category-name">${payload.name}</span>
            <button class="btn btn-small btn-secondary js-edit-category" data-id="${data.id}">Edit</button>
            <button class="btn btn-small btn-danger js-delete-category" data-id="${data.id}">Delete</button>
          `;
          categoryListAdmin.appendChild(li);
        }
        categoryForm.reset();
        if (window.showToast) showToast("Category created.", "success");
      } catch (err) {
        console.error(err);
        alert("Network error while creating category.");
      }
    });
  }

  if (productForm) {
    productForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const formData = new FormData(productForm);
      const payload = {
        name: formData.get("name"),
        price: formData.get("price"),
        category_id: formData.get("category_id"),
      };
      try {
        const res = await fetch("/menu/product", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
          if (window.showToast) showToast(data.error || "Failed to create product", "error");
          return;
        }
        if (productTableBody) {
          const tr = document.createElement("tr");
          tr.dataset.id = data.id;
          tr.innerHTML = `
            <td><span class="product-name">${payload.name}</span></td>
            <td data-category-id="${payload.category_id}"></td>
            <td><span class="product-price" data-price="${parseFloat(payload.price).toFixed(2)}">₹${parseFloat(
              payload.price
            ).toFixed(2)}</span></td>
            <td>
              <button class="btn btn-small btn-secondary js-edit-product" data-id="${data.id}">Edit</button>
              <button class="btn btn-small btn-danger js-delete-product" data-id="${data.id}">Delete</button>
            </td>
          `;
          productTableBody.appendChild(tr);
        }
        productForm.reset();
        if (window.showToast) showToast("Product created.", "success");
      } catch (err) {
        console.error(err);
        alert("Network error while creating product.");
      }
    });
  }

  if (categoryListAdmin) {
    categoryListAdmin.addEventListener("click", async (e) => {
      const editBtn = e.target.closest(".js-edit-category");
      const deleteBtn = e.target.closest(".js-delete-category");
      if (!editBtn && !deleteBtn) return;
      const id = (editBtn || deleteBtn).dataset.id;
      if (deleteBtn) {
        if (!confirm("Delete this category?")) return;
        try {
          const res = await fetch(`/menu/category/${id}`, { method: "DELETE" });
          if (!res.ok) {
            if (window.showToast) showToast("Failed to delete category", "error");
            return;
          }
          deleteBtn.closest("li").remove();
        } catch (err) {
          console.error(err);
          if (window.showToast) showToast("Network error while deleting category.", "error");
        }
      } else if (editBtn) {
        const li = editBtn.closest("li");
        const nameSpan = li.querySelector(".category-name");
        const current = nameSpan.textContent;
        const updated = prompt("Edit category name", current);
        if (!updated || updated === current) return;
        try {
          const res = await fetch(`/menu/category/${id}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name: updated }),
          });
          if (!res.ok) {
            if (window.showToast) showToast("Failed to update category", "error");
            return;
          }
          nameSpan.textContent = updated;
        } catch (err) {
          console.error(err);
          if (window.showToast) showToast("Network error while updating category.", "error");
        }
      }
    });
  }

  if (productTableBody) {
    productTableBody.addEventListener("click", async (e) => {
      const deleteBtn = e.target.closest(".js-delete-product");
      const editBtn = e.target.closest(".js-edit-product");
      if (!deleteBtn && !editBtn) return;
      const id = (deleteBtn || editBtn).dataset.id;
      if (deleteBtn) {
        if (!confirm("Delete this product?")) return;
        try {
          const res = await fetch("/menu/product", {
            method: "DELETE",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ id }),
          });
          if (!res.ok) {
            if (window.showToast) showToast("Failed to delete product", "error");
            return;
          }
          const row = deleteBtn.closest("tr");
          if (row) row.remove();
        } catch (err) {
          console.error(err);
          if (window.showToast) showToast("Network error while deleting product.", "error");
        }
      } else if (editBtn) {
        const row = editBtn.closest("tr");
        const nameSpan = row.querySelector(".product-name");
        const priceSpan = row.querySelector(".product-price");
        const currentName = nameSpan.textContent;
        const currentPrice = priceSpan.dataset.price;
        const newName = prompt("Edit product name", currentName) || currentName;
        const newPrice = prompt("Edit price", currentPrice) || currentPrice;
        try {
          const res = await fetch(`/menu/product/${id}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name: newName, price: newPrice }),
          });
          if (!res.ok) {
            if (window.showToast) showToast("Failed to update product", "error");
            return;
          }
          nameSpan.textContent = newName;
          priceSpan.dataset.price = parseFloat(newPrice).toFixed(2);
          priceSpan.textContent = "₹" + parseFloat(newPrice).toFixed(2);
        } catch (err) {
          console.error(err);
          if (window.showToast) showToast("Network error while updating product.", "error");
        }
      }
    });
  }
});

