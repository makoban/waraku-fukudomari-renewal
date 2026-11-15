const deviceInputs = [...document.querySelectorAll('input[name="device"]')];
const pageFilter = document.querySelector('#page-filter');
const rows = [...document.querySelectorAll('[data-comparison-row]')];
const shots = [...document.querySelectorAll('[data-shot]')];
const params = new URLSearchParams(location.search);
let device = params.get('device') === 'mobile' || (!params.has('device') && matchMedia('(max-width: 719px)').matches) ? 'mobile' : 'desktop';
if ([...pageFilter.options].some(option => option.value === params.get('page'))) pageFilter.value = params.get('page');

function writeUrl() {
  const query = new URLSearchParams();
  query.set('device', device);
  if (pageFilter.value !== 'all') query.set('page', pageFilter.value);
  history.replaceState(null, '', location.pathname + '?' + query + location.hash);
}

function updateStatus() {
  const count = rows.filter(row => !row.hidden).length;
  document.querySelector('#view-status').textContent = `${device === 'mobile' ? 'スマホ 390 × 844' : 'PC 1440 × 1000'} / ${count}画面`;
}

function applyDevice(keepPosition = false) {
  const anchor = keepPosition ? rows.find(row => !row.hidden && row.getBoundingClientRect().bottom > 160) : null;
  const previousTop = anchor?.getBoundingClientRect().top;
  document.body.dataset.device = device;
  deviceInputs.forEach(input => { input.checked = input.value === device; });
  shots.forEach(button => {
    const image = button.querySelector('img');
    const key = device === 'mobile' ? 'mobile' : 'desktop';
    const thumbnail = button.dataset[key + 'Thumbnail'];
    const large = button.dataset[key + 'Large'];
    const width = device === 'mobile' ? 780 : 1440;
    const smallWidth = device === 'mobile' ? 390 : 720;
    image.width = Number(button.dataset[key + 'Width']);
    image.height = Number(button.dataset[key + 'Height']);
    image.srcset = `${thumbnail} ${smallWidth}w, ${large} ${width}w`;
    image.sizes = device === 'mobile' ? '(min-width: 1000px) 390px, 45vw' : '(min-width: 1000px) 560px, 45vw';
    image.src = thumbnail;
    button.closest('figure').querySelector('.original-link').href = button.dataset[key + 'Original'];
  });
  updateStatus();
  writeUrl();
  if (anchor) requestAnimationFrame(() => scrollBy(0, anchor.getBoundingClientRect().top - previousTop));
}

function applyFilter(scroll = false) {
  rows.forEach(row => { row.hidden = pageFilter.value !== 'all' && row.dataset.page !== pageFilter.value; });
  updateStatus();
  writeUrl();
  if (scroll) document.querySelector('#comparisons').scrollIntoView({block: 'start'});
}

deviceInputs.forEach(input => input.addEventListener('change', () => { device = input.value; applyDevice(true); }));
pageFilter.addEventListener('change', () => applyFilter(true));
document.querySelectorAll('[data-show-screen]').forEach(button => button.addEventListener('click', () => { pageFilter.value = button.dataset.showScreen; applyFilter(true); }));
document.querySelectorAll('.row-anchor').forEach(link => link.addEventListener('click', () => { pageFilter.value = link.closest('[data-comparison-row]').dataset.page; applyFilter(); }));
document.querySelector('#print-button').addEventListener('click', () => window.print());
new ResizeObserver(entries => { document.documentElement.style.setProperty('--toolbar-height', `${entries[0].target.getBoundingClientRect().height}px`); }).observe(document.querySelector('.toolbar-shell'));

const zoom = document.querySelector('#zoom-dialog');
const zoomImage = document.querySelector('#zoom-image');
shots.forEach(button => button.addEventListener('click', () => {
  const large = button.dataset[device + 'Large'];
  const original = button.dataset[device + 'Original'];
  const title = button.getAttribute('aria-label').replace('のスクリーンショットを拡大', '') + (device === 'mobile' ? ' / スマホ' : ' / PC');
  document.querySelector('#zoom-title').textContent = title;
  zoomImage.src = large;
  zoomImage.alt = title + 'の実際のスクリーンショット';
  document.querySelector('#zoom-original').href = original;
  document.querySelector('#zoom-new-tab').href = original;
  zoom.showModal();
}));
document.querySelector('#zoom-close').addEventListener('click', () => zoom.close());
zoom.addEventListener('click', event => {
  const rect = zoom.getBoundingClientRect();
  if (event.target === zoom && (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom)) zoom.close();
});
zoom.addEventListener('close', () => zoomImage.removeAttribute('src'));
applyDevice();
applyFilter();
