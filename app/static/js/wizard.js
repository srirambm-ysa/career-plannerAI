document.addEventListener('DOMContentLoaded', function () {
    var taskForm = document.getElementById('task-form');
    var taskList = document.getElementById('task-list');
    var addBtn = document.getElementById('add-task-btn');
    var suggestBtn = document.getElementById('suggest-tasks-btn');
    var submitBtn = document.getElementById('submit-tasks');
    var taskCount = document.getElementById('task-count');
    var jobTitleInput = document.getElementById('job_title');
    var yearsExpInput = document.getElementById('years_exp');
    var industry = document.getElementById('industry');

    var suggestionMap = {};
    var placeholderIndex = 0;

    function escapeHtml(str) {
        var div = document.createElement('div');
        div.appendChild(document.createTextNode(str));
        return div.innerHTML;
    }

    function updateCount() {
        var inputs = taskList.querySelectorAll('.task-input');
        var filled = 0;
        inputs.forEach(function (inp) {
            if (inp.value.trim()) filled++;
        });
        if (taskCount) {
            taskCount.textContent = filled + ' of ' + inputs.length + ' tasks';
        }
    }

    function renumberPlaceholders() {
        var items = taskList.querySelectorAll('.task-placeholder');
        items.forEach(function (item, idx) {
            var label = item.querySelector('.placeholder-label');
            if (label) label.textContent = 'Task ' + (idx + 1);
        });
    }

    function addTaskPlaceholder(description) {
        var idx = placeholderIndex++;
        var div = document.createElement('div');
        div.className = 'task-placeholder flex items-start gap-3 bg-white rounded-xl border border-slate-200 p-4';
        div.dataset.index = idx;
        div.innerHTML =
            '<span class="placeholder-label text-xs font-semibold text-slate-400 w-14 pt-2 flex-shrink-0">Task ' + (taskList.children.length + 1) + '</span>' +
            '<div class="flex-1 min-w-0">' +
                '<input type="text" name="task_desc" class="task-input w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none" placeholder="Enter task description..." value="' + escapeHtml(description || '') + '">' +
            '</div>' +
            '<button type="button" class="remove-task text-slate-400 hover:text-red-500 transition-colors flex-shrink-0 pt-2">&times;</button>';
        taskList.appendChild(div);

        var input = div.querySelector('.task-input');
        input.addEventListener('input', updateCount);

        div.querySelector('.remove-task').addEventListener('click', function () {
            for (var key in suggestionMap) {
                if (suggestionMap[key] === input) {
                    delete suggestionMap[key];
                    var cb = document.querySelector('.suggest-checkbox[data-sugg-index="' + key + '"]');
                    if (cb) cb.checked = false;
                }
            }
            div.remove();
            renumberPlaceholders();
            updateCount();
        });

        updateCount();
        renumberPlaceholders();
        return input;
    }

    if (addBtn && taskForm) {
        addBtn.addEventListener('click', function () {
            addTaskPlaceholder('');
        });
    }

    if (suggestBtn) {
        suggestBtn.addEventListener('click', function () {
            var title = jobTitleInput ? jobTitleInput.value.trim() : '';
            if (!title) {
                jobTitleInput.focus();
                jobTitleInput.style.borderColor = '#ef4444';
                setTimeout(function () { jobTitleInput.style.borderColor = ''; }, 2000);
                return;
            }
            var loadingEl = document.getElementById('suggested-loading');
            var modalEl = document.getElementById('suggested-modal');
            var listEl = document.getElementById('suggested-list');

            loadingEl.classList.remove('hidden');

            var payload = {
                job_title: title,
                industry: industry ? industry.value : '',
                years_exp: yearsExpInput ? parseInt(yearsExpInput.value) || 0 : 0
            };

            fetch('/assessment/step/2/suggest-tasks', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            })
            .then(function (res) { return res.json(); })
            .then(function (data) {
                loadingEl.classList.add('hidden');
                var tasks = data.tasks || [];
                if (tasks.length === 0) {
                    listEl.innerHTML = '<p class="text-sm text-slate-500 py-4 text-center">No suggestions available.</p>';
                } else {
                    listEl.innerHTML = '';
                    tasks.forEach(function (task, i) {
                        var label = document.createElement('label');
                        label.className = 'flex items-start gap-3 p-2 rounded-lg hover:bg-slate-50 cursor-pointer transition-colors';
                        var cb = document.createElement('input');
                        cb.type = 'checkbox';
                        cb.className = 'suggest-checkbox mt-0.5 w-4 h-4 text-blue-600 border-slate-300 rounded focus:ring-blue-500 flex-shrink-0';
                        cb.dataset.suggIndex = i;
                        cb.dataset.description = task.description;
                        if (suggestionMap[i]) {
                            cb.checked = true;
                        }
                        var descSpan = document.createElement('div');
                        descSpan.className = 'flex-1 min-w-0';
                        descSpan.innerHTML = '<p class="text-sm text-slate-900">' + escapeHtml(task.description) + '</p>' +
                            (task.category ? '<span class="inline-block mt-0.5 px-2 py-0.5 bg-slate-100 text-slate-600 text-xs font-medium rounded">' + escapeHtml(task.category) + '</span>' : '');
                        label.appendChild(cb);
                        label.appendChild(descSpan);
                        listEl.appendChild(label);

                        cb.addEventListener('change', function () {
                            var _cb = this;
                            var idx = parseInt(_cb.dataset.suggIndex);
                            var desc = _cb.dataset.description;
                            if (_cb.checked) {
                                var inputs = taskList.querySelectorAll('.task-input');
                                var target = null;
                                for (var j = 0; j < inputs.length; j++) {
                                    if (!inputs[j].value.trim()) {
                                        target = inputs[j];
                                        break;
                                    }
                                }
                                if (target) {
                                    target.value = desc;
                                    suggestionMap[idx] = target;
                                    target.dispatchEvent(new Event('input'));
                                } else {
                                    var newInput = addTaskPlaceholder(desc);
                                    suggestionMap[idx] = newInput;
                                }
                            } else {
                                var mappedInput = suggestionMap[idx];
                                if (mappedInput && mappedInput.closest('.task-placeholder')) {
                                    mappedInput.value = '';
                                    mappedInput.dispatchEvent(new Event('input'));
                                }
                                delete suggestionMap[idx];
                            }
                        });
                    });
                }
                modalEl.classList.remove('hidden');
            })
            .catch(function () {
                loadingEl.classList.add('hidden');
                listEl.innerHTML = '<p class="text-sm text-red-500 py-4 text-center">Failed to load suggestions. Please try again.</p>';
                modalEl.classList.remove('hidden');
            });
        });
    }

    var closeModalBtn = document.getElementById('close-modal-btn');
    var doneModalBtn = document.getElementById('done-modal-btn');
    var modalEl = document.getElementById('suggested-modal');

    function closeModal() {
        if (modalEl) modalEl.classList.add('hidden');
    }

    if (closeModalBtn) closeModalBtn.addEventListener('click', closeModal);
    if (doneModalBtn) doneModalBtn.addEventListener('click', closeModal);
    if (modalEl) {
        modalEl.addEventListener('click', function (e) {
            if (e.target === modalEl) closeModal();
        });
    }

    if (submitBtn && taskForm) {
        submitBtn.addEventListener('click', function (e) {
            var inputs = taskList.querySelectorAll('.task-input');
            var filled = 0;
            inputs.forEach(function (inp) {
                if (inp.value.trim()) filled++;
            });
            if (filled === 0) {
                e.preventDefault();
                alert('Please add at least one task.');
                return;
            }
            if (!taskForm.checkValidity()) return;
            setTimeout(function () {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span class="spinner"></span> Evaluating...';
            }, 50);
        });
    }

    var resultsList = document.getElementById('results-list');
    if (resultsList) {
        resultsList.querySelectorAll('div.bg-white, div.bg-green-50\\/30, div.bg-amber-50\\/30, div.bg-red-50\\/30').forEach(function (el, i) {
            el.style.opacity = '0';
            setTimeout(function () {
                el.style.opacity = '1';
            }, i * 80);
        });
    }

    var formSubmits = document.querySelectorAll('form button[type="submit"]');
    formSubmits.forEach(function (btn) {
        btn.addEventListener('click', function (e) {
            var form = btn.closest('form');
            if (form && form.checkValidity && !form.checkValidity()) {
                return;
            }
            if (!btn.disabled && btn.id === 'submit-tasks') {
                return;
            }
            if (!btn.disabled && !btn.dataset.noLoading) {
                setTimeout(function () {
                    btn.disabled = true;
                    btn.innerHTML = '<span class="spinner"></span> Processing...';
                }, 50);
            }
        });
    });

    var clearBtn = document.getElementById('clear-tasks-btn');
    if (clearBtn && taskList) {
        clearBtn.addEventListener('click', function () {
            if (taskList.children.length === 0) return;
            taskList.innerHTML = '';
            suggestionMap = {};
            placeholderIndex = 0;
            updateCount();
        });
    }

    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') {
            var modal = document.getElementById('suggested-modal');
            if (modal && !modal.classList.contains('hidden')) {
                modal.classList.add('hidden');
            }
        }
    });
});
