
function updateFileName(input) {
    const fileName = input.files[0]?.name || 'Файл не выбран';
    const textElement = input.parentElement.querySelector('.file-input-text');
    textElement.textContent = fileName;
    textElement.style.color = '#2c3e50';
}


    const checkboxes = document.querySelectorAll('.sentence-checkbox');
    const bulkActions = document.querySelector('.bulk-actions');
    const selectedCount = document.getElementById('selectedCount');

    function updateSelection() {
        const selected = document.querySelectorAll('.sentence-checkbox:checked').length;
        selectedCount.textContent = selected;
        bulkActions.classList.toggle('show', selected > 0);
    }

    function copySelectedTexts() {
        const selected = Array.from(document.querySelectorAll('.sentence-checkbox:checked'))
            .map(checkbox => checkbox.dataset.text)
            .join('\n\n');

        if (!selected) {
            alert('Выберите хотя бы одно предложение для копирования');
            return;
        }

        navigator.clipboard.writeText(selected)
            .then(() => {
                alert('Скопировано ' + selectedCount.textContent + ' предложений');
                checkboxes.forEach(cb => cb.checked = false);
                updateSelection();
            })
            .catch(err => {
                console.error('Ошибка копирования:', err);
                alert('Не удалось скопировать текст');
            });
    }

    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', updateSelection);
    });
