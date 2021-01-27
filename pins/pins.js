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
})();
