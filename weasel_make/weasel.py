#!/usr/bin/env python3

import os
import sys
import subprocess
import re
import argparse
import math
import tty
import termios

local_vars = {}
recording_file = None
filter_secrets = True
istty = False
console_width = 100
max_history = 1000

def calculate_shannon_entropy(s):
	entropy = 0.0
	s = re.sub(r'\s+', '', s)
	for x in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-+/':
		p_x = float(s.count(x)) / len(s)
		if p_x > 0:
			entropy += - p_x * math.log(p_x, 2)
	if len(s) > 2:
		entropy -= 1.2 / math.log(len(s), 2)
	return entropy

def filter_secrets_from_string(s):
	if len(s) > 8 and calculate_shannon_entropy(s) > 4.5:
		return re.sub(r'[abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_\-+/]', '*', s)
	return s

def strip_comments(lines):
	return [ s[:s.index('#')] if '#' in s else s for s in lines ]

def concatenate_follow_lines(lines):
	if len(lines) == 0:
		return []

	ls = [ lines[0] ]
	for l in lines[1:]:
		if ls[-1].endswith('\\\n'):
			ls[-1] = ls[-1][:-2] + ' ' + l
		else:
			ls.append(l)
	return ls

def process_lines(lines):
	lines = strip_comments(lines)
	lines = concatenate_follow_lines(lines)
	# lines = [ s.strip() for s in lines ]
	lines = [ s.replace('\n', ' ') for s in lines ]
	# lines = list(filter(lambda s: s != '', lines))
	return lines

def group_makefile_commands(lines):
	groups = { '': {'group_words': [], 'commands': []} }
	group_word = None
	for l in lines:
		if re.match(r"^\w+:\s*(\w+(\s+\w+)*)?\s*$", l):
			group_word = l.split(':')[0]
			if group_word not in groups:
				groups[group_word] = {'group_words': [], 'commands': []}
			words = filter(lambda s: s != '', re.split(r'\s+', l.split(':')[1]))
			for word in words:
				groups[group_word]['group_words'].append(word)
		elif re.match(r"^\s*$", l):
			pass
		elif l.startswith('\t'):
			groups[group_word]['commands'].append(l[1:].strip())
		else:
			groups['']['commands'].append(l.strip())

	return groups

def load_makefile(filepath):
	with open(filepath, 'r') as f:
		lines = process_lines(f.readlines())
	groups = group_makefile_commands(lines)
	execute_makefile_precommands(groups['']['commands'])
	return groups

display_offset = 0
display_buffer = []
display_history = []
log_length=40

def clean_display():
	global display_offset, display_buffer, display_history
	if len(display_buffer) > 0:
		print("\033[" + str(len(display_buffer)) + "A", end='')

def clean_display2():
	global display_offset, display_buffer, display_history
	if len(display_buffer) > 0:
		print("\033[" + str(len(display_buffer-1)) + "A", end='')

def redisplay_history():
	global display_offset, display_buffer, display_history

	if len(display_history) > log_length:
		display_buffer = display_history[:len(display_history)-display_offset][-log_length:]
	else:
		display_buffer = display_history

	for l in display_buffer:
		print("\033[K" + l)

def execute_shell_command(command):
	global log_length
	global proc, display_offset, display_buffer, display_history
	# run the command with pipefail on
	# nosemgrep
	proc = subprocess.Popen('bash -o pipefail -c "' + command + '" 2>&1', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

	display_offset = 0
	display_buffer = []
	display_history = []

	# read output line by line
	for line in iter(proc.stdout.readline, ""):
		if recording_file is not None:
			recording_file.write(line)

		if istty:
			line = line.replace('\n', '')
			if filter_secrets:
				line = filter_secrets_from_string(line)
			# Break line into chunks of console_width
			line_chunks = [line[i:i + console_width] for i in range(0, len(line), max(console_width, 20))]

			# i have no clue why the order is like this, but it breaks otherwise
			clean_display()

			# Append each chunk to the history
			for chunk in line_chunks:
				display_history.append(chunk)
				# cap history length at max_history
				if len(display_history) > max_history:
					display_history = display_history[1:]

			redisplay_history()

		else:
			print(line, end='')

	# wait for status
	status = proc.wait()
	proc = None

	# if success, erase output and print ok
	if status == 0:
		if istty:
			print("\r\033[K", end='')
			for i in range(len(display_buffer)):
				print("\033[1A\033[K", end='')
			print("\33[1m\33[92m" + command + " - ok!" + "\033[0m")
		else:
			print(command + " - ok!")
	return status

def execute_makefile_precommands(commands):
	for command in commands:
		if m := re.match(r"^(\w+)\s*=\s*(.*)$", command):
			local_vars[m.group(1)] = m.group(2)
		elif m := re.match(r"^include\s*(.+)$", command):
			load_makefile(m.group(1))
		elif command == 'export':
			for key in local_vars:
				os.environ[key] = local_vars[key]
		else:
			raise Exception('invalid command in make precommands: ' + command)
	return True

def execute_makefile_commands(commands):
	for command in commands:
		if m := re.match(r"^(\w+)\s*=\s*(.*)$", command):
			local_vars[m.group(1)] = m.group(2)
		else:
			ignore_status = False
			if command.startswith('-'):
				command = command[1:]
				ignore_status = True
			status = execute_shell_command(command)
			if status != 0 and not ignore_status:
				if istty:
					print('\33[1m\33[101m' + 'error: "' + command + '" exited with status ' + str(status) + "\033[0m")
				else:
					print('error: "' + command + '" exited with status ' + str(status))
				sys.exit(status)

def execute_makefile_group(groups, groupname):
	if groups.get(groupname) is None:
		print(f"Error: Target '{groupname}' not found in the makefile.", file=sys.stderr)
		sys.exit(1)

	for group_word in groups[groupname]['group_words']:
		execute_makefile_group(groups, group_word)
	execute_makefile_commands(groups[groupname]['commands'])

import threading
import select

stop_input_thread = False

def capture_input():
	global istty, proc, stop_input_thread, display_offset, display_buffer, display_history
	if not istty:
		return

	stop_input_thread = False

	old_settings = termios.tcgetattr(sys.stdin)
	try:
		tty.setcbreak(sys.stdin.fileno())
		while not stop_input_thread:
			read_list, _, _ = select.select([sys.stdin], [], [], 0.05)
			if read_list:
				char = sys.stdin.read(1)
				# check for special characters
				if char == '\x03':  # Ctrl+C
					break
				elif char == '\x1b':  # Arrow keys
					char += sys.stdin.read(2)
					if char == '\x1b[A':  # Up arrow
						display_offset = min(len(display_history) - 1, display_offset + 1)
					elif char == '\x1b[B':  # Down arrow
						display_offset = max(0, display_offset - 1)
					clean_display()
					redisplay_history()

				# else pass the character to an existing process
				elif proc:
					proc.stdin.write(char)
					proc.stdin.flush()
					print(char, end='', flush=True)

					if char == '\n':  # Enter key resets the display offset
						display_offset = 0
	finally:
		termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)


def run_weasel_make(filepath, grouptargets):
	global istty, stop_input_thread
	groups = load_makefile(filepath)
	input_thread = threading.Thread(target=capture_input)
	input_thread.start()
	try:
		for arg in grouptargets:
			execute_makefile_group(groups, arg)
	finally:
		stop_input_thread = True
		input_thread.join()

def main():
	global recording_file, istty, console_width

	# wrap to catch sigint
	try:
		if sys.stdout.isatty():
			istty = True
			console_width = os.get_terminal_size().columns
		else:
			istty = False

		# parse arguments
		parser = argparse.ArgumentParser(prog='weasel', description='An obscureful build tool')
		parser.add_argument('targets', metavar='target', type=str, nargs='*',
							help='list of targets to run')
		parser.add_argument('-o', '--output', help='specifies a filepath to duplicate output to')
		parser.add_argument('-v', '--version', action='store_true', help='prints the weasel-make version')
		parser.add_argument('-f', '--file', default='Makefile', help='specifies the makefile path to use')
		parser.add_argument('--bash-autocompletions-source', action='store_true', help='prints a static bash script for weasel auto-completions')
		args = parser.parse_args()

		if args.output is not None:
			recording_file = open(args.output, 'a')

		if args.bash_autocompletions_source:
			print('''
_weasel_autocomplete()
{
	local cur opts makefile_opts
	cur="${COMP_WORDS[COMP_CWORD]}"
	makefile_opts=$(cat Makefile | grep -Po '^\\S+(?=:)' | xargs)
	opts="$makefile_opts"
	COMPREPLY=( $(compgen -W "$opts" -- "$cur" | xargs) )
	return 0
}
complete -F _weasel_autocomplete weasel
''')
			sys.exit(0)
			return

		if args.version:
			print("weasel-make v0.3.2")
			sys.exit(0)
			return

		if args.targets:
			run_weasel_make(args.file, args.targets)
		else:
			parser.error("the following arguments are required: target")
		sys.exit(0)

	except KeyboardInterrupt:
		sys.exit(1)

if __name__ == '__main__':
	main()
