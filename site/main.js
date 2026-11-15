const menuDialog = document.querySelector('#site-menu');
const imageDialog = document.querySelector('#image-dialog');
const enlargedImage = document.querySelector('#enlarged-image');
const imageCaption = document.querySelector('#image-caption');

document.querySelector('[data-open-menu]')?.addEventListener('click', () => {
  menuDialog.showModal();
});

document.querySelectorAll('[data-close-dialog]').forEach((button) => {
  button.addEventListener('click', () => button.closest('dialog').close());
});

document.querySelectorAll('dialog').forEach((dialog) => {
  dialog.addEventListener('click', (event) => {
    if (event.target !== dialog) return;
    const box = dialog.getBoundingClientRect();
    if (event.clientX < box.left || event.clientX > box.right || event.clientY < box.top || event.clientY > box.bottom) dialog.close();
  });
});

menuDialog.querySelectorAll('a[href^="#"]').forEach((link) => {
  link.addEventListener('click', () => menuDialog.close());
});

document.querySelectorAll('[data-image]').forEach((button) => {
  button.addEventListener('click', () => {
    enlargedImage.src = button.dataset.image;
    enlargedImage.alt = button.dataset.caption;
    imageCaption.textContent = button.dataset.caption;
    imageDialog.showModal();
  });
});

imageDialog.addEventListener('close', () => {
  enlargedImage.removeAttribute('src');
});

const searchInput = document.querySelector('#blog-search');
if (searchInput) {
  const monthInput = document.querySelector('#blog-month');
  const cards = [...document.querySelectorAll('[data-blog-card]')];
  const count = document.querySelector('#blog-result-count');
  const pageStatus = document.querySelector('#blog-page-status');
  const previous = document.querySelector('#blog-prev');
  const next = document.querySelector('#blog-next');
  const empty = document.querySelector('#blog-empty');
  const params = new URLSearchParams(location.search);
  searchInput.value = params.get('q') || '';
  monthInput.value = params.get('month') || '';
  let currentPage = 0;
  const pageSize = 12;
  const normalize = (text) => text.normalize('NFKC').toLocaleLowerCase('ja');
  function showResults(resetPage = false, moveToResults = false) {
    if (resetPage) currentPage = 0;
    const terms = normalize(searchInput.value.trim()).split(/\s+/).filter(Boolean);
    const month = monthInput.value;
    const filtered = cards.filter((card) => (!month || card.dataset.month === month) && terms.every((term) => normalize(card.dataset.search).includes(term)));
    const pages = Math.max(1, Math.ceil(filtered.length / pageSize));
    currentPage = Math.min(currentPage, pages - 1);
    const visible = new Set(filtered.slice(currentPage * pageSize, (currentPage + 1) * pageSize));
    cards.forEach((card) => { card.hidden = !visible.has(card); });
    count.textContent = `${filtered.length}件の記事`;
    pageStatus.textContent = `${currentPage + 1} / ${pages}`;
    previous.disabled = currentPage === 0;
    next.disabled = currentPage + 1 >= pages;
    empty.hidden = filtered.length > 0;
    const query = new URLSearchParams();
    if (searchInput.value.trim()) query.set('q', searchInput.value.trim());
    if (month) query.set('month', month);
    history.replaceState(null, '', location.pathname + (query.size ? '?' + query : '') + location.hash);
    if (moveToResults) document.querySelector('#blog-result-count').scrollIntoView({block: 'start'});
  }
  searchInput.addEventListener('input', () => showResults(true));
  monthInput.addEventListener('change', () => showResults(true));
  document.querySelector('#blog-reset').addEventListener('click', () => {
    searchInput.value = '';
    monthInput.value = '';
    showResults(true);
    searchInput.focus();
  });
  previous.addEventListener('click', () => { currentPage--; showResults(false, true); });
  next.addEventListener('click', () => { currentPage++; showResults(false, true); });
  showResults();
}
