# Tool catalog

The server currently registers 63 MCP tools.

## Portal and system status

- `hello`
- `portal_status`
- `system_summary`
- `disk_summary`
- `current_directory`
- `which`
- `check_port`
- `environment_variables` (redacts names containing token, secret, password, or key)
- `ngrok_status` (legacy/local diagnostic only)

## Files

- `list_directory`
- `file_info`
- `read_text_file`
- `tail_text_file`
- `find_files`
- `search_text_in_files`
- `list_available_paths`
- `path_access`
- `read_text_range`
- `hash_file`
- `write_text_file` — requires `confirm='WRITE_FILE'`
- `append_text_file` — requires `confirm='APPEND_FILE'`

## Processes, commands, and Python

- `list_processes`
- `kill_process` — requires `confirm='KILL_PID'`
- `run_powershell`
- `run_cmd`
- `python_version`
- `python_import_check`
- `pip_list`

### Persistent background jobs

- `start_job` — requires `START_JOB` for read-only commands or `START_MUTATING_JOB` when mutation is detected
- `list_jobs`
- `job_status`
- `job_output`
- `stop_job` — requires `STOP_JOB`
- `delete_job` — requires `DELETE_JOB`

Each background job runs in an independent worker and stores bounded metadata plus separate stdout/stderr logs under the configured job directory. Multiple jobs can run concurrently. Use a timeout for unattended work and delete finished records when their logs are no longer needed.

The command tools reject a small set of dangerous system-wide commands. Commands that appear mutating require `confirm='RUN_MUTATING_COMMAND'`. This is a convenience interlock, not a substitute for endpoint security or ChatGPT approval settings.

## Desktop observation

- `desktop_operator_status`
- `capture_screen`
- `annotate_screen`
- `get_mouse_position`
- `desktop_windows`
- `capture_window`
- `list_ui_elements`
- `ocr_screen`
- `find_text_on_screen`
- `find_image_on_screen`
- `wait_for_window`

## Desktop control

These require `confirm='CONTROL_DESKTOP'`:

- `move_mouse`
- `left_click`
- `right_click`
- `double_click`
- `drag_mouse`
- `press_key`
- `hotkey`
- `type_text`
- `click_ui_element`
- `click_text`
- `click_image_on_screen`
- `close_window`

These window actions do not currently require the confirmation value but do change visible desktop state:

- `activate_window`
- `maximize_window`
- `minimize_window`

## Application launching

- `launch_program` — requires `confirm='LAUNCH_PROGRAM'`
- `launch_start_app` — requires `confirm='LAUNCH_PROGRAM'`
- `computer_help`
