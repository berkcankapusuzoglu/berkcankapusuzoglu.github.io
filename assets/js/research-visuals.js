(() => {
  const motion = window.matchMedia('(prefers-reduced-motion: reduce)');
  document.querySelectorAll('[data-research-sequence]').forEach((sequence) => {
    const frames = [...sequence.querySelectorAll('[data-sequence-frame]')];
    const steps = [...sequence.querySelectorAll('[data-sequence-step]')];
    const button = sequence.querySelector('[data-sequence-control]');
    const status = sequence.querySelector('[data-sequence-status]');
    if (frames.length < 2 || !button || !status) return;

    let index = frames.length - 1;
    let timer = null;
    let playing = false;
    const duration = () => Number(frames[index].dataset.duration) || 1800;
    const describe = (suffix = '') => {
      status.textContent = `Step ${index + 1} of ${frames.length}: ${frames[index].dataset.label}.${suffix ? ` ${suffix}` : ''}`;
      button.textContent = motion.matches ? 'Next step' : playing ? 'Pause sequence' : 'Play sequence';
    };
    const show = (next) => {
      index = next;
      frames.forEach((frame, position) => { frame.hidden = position !== index; });
      steps.forEach((step, position) => {
        if (position === index) step.setAttribute('aria-current', 'step');
        else step.removeAttribute('aria-current');
      });
      describe(index === frames.length - 1 ? 'Final frame.' : '');
    };
    const pause = (suffix = 'Paused.') => {
      clearTimeout(timer);
      timer = null;
      playing = false;
      describe(suffix);
    };
    const advance = () => {
      if (motion.matches || document.hidden) { pause(); return; }
      show(index + 1);
      if (index === frames.length - 1) pause('Final frame. Sequence complete.');
      else timer = setTimeout(advance, duration());
    };

    button.disabled = false;
    describe('Final frame.');
    button.addEventListener('click', () => {
      if (motion.matches) {
        pause('');
        show(index === frames.length - 1 ? 0 : index + 1);
      } else if (playing) pause();
      else {
        if (document.hidden) return;
        if (index === frames.length - 1) show(0);
        playing = true;
        describe('Playing.');
        timer = setTimeout(advance, duration());
      }
    });
    motion.addEventListener('change', () => pause(motion.matches ? 'Reduced motion: use Next step.' : 'Paused.'));
    document.addEventListener('visibilitychange', () => { if (document.hidden) pause('Paused while the page is hidden.'); });
    window.addEventListener('beforeprint', () => pause('Paused for printing.'));
  });
})();
