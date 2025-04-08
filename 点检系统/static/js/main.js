document.addEventListener('keydown', function(event) {
  switch(event.key) {
    case 'ArrowUp': case 'ArrowDown':
      event.preventDefault();
      const inputs = document.querySelectorAll('input, select, textarea');
      const current = document.activeElement;
      const index = Array.from(inputs).indexOf(current);
      if (event.key === 'ArrowDown' && index < inputs.length - 1) inputs[index + 1].focus();
      if (event.key === 'ArrowUp' && index > 0) inputs[index - 1].focus();
      break;
    case 'Enter':
      document.querySelector('form').submit();
      break;
    case 'Escape':
      window.history.back();
      break;
    case 'F1':
      document.querySelector('button[type="submit"]').click();
      break;
    case 'F2':
      addCustomItem();
      break;
    case '1':
      document.querySelector('#mode-work')?.click();
      break;
    case '2':
      document.querySelector('#mode-standby')?.click();
      break;
    case '3':
      document.querySelector('#mode-charging')?.click();
      break;
  }
});