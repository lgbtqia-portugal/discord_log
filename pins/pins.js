'use strict';
(() => {
	for (const h1 of document.querySelectorAll('h1')) {
		h1.addEventListener('click', (event) => {
			const section = event.target.nextElementSibling;
			if (section.classList.contains('hidden'))
				section.classList.remove('hidden');
			else
				section.classList.add('hidden');
		});
	}

	const modal = document.querySelector('#modal');
	for (const img of document.querySelectorAll('div.pin div.bottom_content img')) {
		img.addEventListener('click', (event) => {
			modal.innerHTML = '';
			const modal_img = document.createElement('img');
			modal_img.src = event.target.src;
			modal.appendChild(modal_img);
			modal.style.display = 'flex';
		});
	}
	modal.addEventListener('click', (event) => {
		if (event.target === modal)
			modal.style.display = 'none';
	});
})();
