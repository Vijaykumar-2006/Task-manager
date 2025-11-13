document.addEventListener('DOMContentLoaded', () => {

  // ------------------------------
  // Drag & Drop Reordering
  // ------------------------------
  let dragSrcEl = null;

  function handleDragStart(e) {
    dragSrcEl = this;
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', this.dataset.id);
    this.classList.add('dragging');
  }

  function handleDragOver(e) {
    if (e.preventDefault) e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    return false;
  }

  function handleDragEnter() {
    this.classList.add('over');
  }

  function handleDragLeave() {
    this.classList.remove('over');
  }

  function handleDrop(e) {
    if (e.stopPropagation) e.stopPropagation();
    const srcId = e.dataTransfer.getData('text/plain');
    const destId = this.dataset.id;

    if (srcId !== destId) {
      const tbody = this.parentNode;
      const srcRow = tbody.querySelector(`tr[data-id='${srcId}']`);
      tbody.insertBefore(srcRow, this.nextSibling);

      // Save new order to backend
      const order = Array.from(tbody.querySelectorAll('tr')).map(tr => tr.dataset.id);
      fetch('/api/reorder', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ order })
      });
    }
    return false;
  }

  function handleDragEnd() {
    this.classList.remove('dragging');
    document.querySelectorAll('#taskBody tr').forEach(tr => tr.classList.remove('over'));
  }

  const rows = document.querySelectorAll('#taskBody tr');
  rows.forEach(row => {
    row.addEventListener('dragstart', handleDragStart);
    row.addEventListener('dragenter', handleDragEnter);
    row.addEventListener('dragover', handleDragOver);
    row.addEventListener('dragleave', handleDragLeave);
    row.addEventListener('drop', handleDrop);
    row.addEventListener('dragend', handleDragEnd);
  });

  // ------------------------------
  // Row Selection on Checkbox
  // ------------------------------
  function updateRowSelection(checkbox) {
    const row = checkbox.closest('tr');
    if (checkbox.checked) {
      row.classList.add('selected');
    } else {
      row.classList.remove('selected');
    }
  }

  document.querySelectorAll('.task-checkbox').forEach(cb => {
    updateRowSelection(cb); // initialize
    cb.addEventListener('change', () => updateRowSelection(cb));
  });

  // ------------------------------
  // Select All Checkbox
  // ------------------------------
  const selectAll = document.getElementById('select-all');
  selectAll.addEventListener('change', () => {
    const checked = selectAll.checked;
    document.querySelectorAll('.task-checkbox').forEach(cb => {
      cb.checked = checked;
      updateRowSelection(cb);
    });
  });

  // ------------------------------
  // Bulk Actions
  // ------------------------------
  async function bulkAction(action) {
    const ids = Array.from(document.querySelectorAll('.task-checkbox:checked'))
      .map(cb => cb.dataset.id);
    if (!ids.length) {
      alert('No tasks selected.');
      return;
    }

    if (action === 'delete' && !confirm('Are you sure you want to delete selected tasks?')) return;

    const res = await fetch('/api/bulk_action', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ids, action })
    });

    const data = await res.json();
    if (data.success) {
      if (action === 'delete') {
        data.updated.forEach(id => {
          const row = document.querySelector(`#taskBody tr[data-id='${id}']`);
          if (row) row.remove();
        });
      } else {
        data.updated.forEach(id => {
          const row = document.querySelector(`#taskBody tr[data-id='${id}']`);
          if (row) {
            const statusCell = row.querySelector('td:nth-child(7)');
            statusCell.innerText = action === 'complete' ? 'completed' : 'pending';
          }
        });
      }
    }
  }

  document.getElementById('bulk-delete')?.addEventListener('click', () => bulkAction('delete'));
  document.getElementById('bulk-complete')?.addEventListener('click', () => bulkAction('complete'));

});
