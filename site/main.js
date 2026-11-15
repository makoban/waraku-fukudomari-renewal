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
