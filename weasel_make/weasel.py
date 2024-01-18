#!/usr/bin/env python3

import os
import sys
import subprocess
import re
import argparse
import math



local_vars = {}
recording_file = None
filter_secrets = True
istty = False
console_width = 100

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
	groups = { '': [] }
	group_word = None
	for l in lines:
		if re.match(r"^\w+:\s*(\w+(\s+\w+)*)?\s*$", l):
			group_word = l.split(':')[0]
			groups[group_word] = groups.get(group_word) or []
			# print(group_word, groups[group_word])
			words = filter(lambda s: s != '', re.split(r'\s+', l.split(':')[1]))
			for word in words:
				groups[group_word].append('weasel ' + word)
		elif re.match(r"^\s*$", l):
			pass
		elif l.startswith('\t'):
			# print(l)
			groups[group_word].append(l[1:].strip())
		else:
			groups[''].append(l.strip())

	return groups


def load_makefile(filepath):
	with open(filepath, 'r') as f:
		lines = process_lines(f.readlines())
	# print(lines)
	groups = group_makefile_commands(lines)
	# print(groups)

	execute_makefile_precommands(groups[''])

	return groups

def execute_shell_command(command, log_length=40):
	# run the command with pipefail on
	proc = subprocess.Popen('bash -o pipefail -c "' + command + '" 2>&1',
			shell=True,
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE,
			universal_newlines=True)

	last_lines = []

	# read output line by line
	for line in iter(proc.stdout.readline, ""):
		if recording_file is not None:
			recording_file.write(line)

		if istty:
			line = line.replace('\n', '')
			if filter_secrets:
				line = filter_secrets_from_string(line)

			if len(last_lines) > 0:
				print("\033[" + str(len(last_lines)) + "A", end='')

			if len(line) > console_width:
				line = line[:console_width]
			last_lines.append(line)
			if len(last_lines) > log_length:
				last_lines = last_lines[1:]
			for l in last_lines:
				print("\033[K" + l)
		else:
			print(line, end='')

	# wait for status
	status = proc.wait()

	# if success, erase output and print ok
	if status == 0:
		if istty:
			for i in range(len(last_lines)):
				print("\033[1A\033[K", end='')
			print("\33[1m\33[92m" + command + " - ok!" + "\033[0m")
		else:
			print(command + " - ok!")
	return status

def execute_makefile_precommands(commands):
	for command in commands:
		if m := re.match(r"^(\w+)\s*=\s*(.*)$", command):
			local_vars[m.group(1)] = m.group(2)
			# print("set var:", m.group(1), '=', m.group(2))
		elif m := re.match(r"^include\s*(.+)$", command):
			load_makefile(m.group(1))
		elif command == 'export':
			for key in local_vars:
				os.environ[key] = local_vars[key]
		else:
			raise 'invalid command in make precommands: ' + command
	return True

def execute_makefile_commands(commands):
	for command in commands:
		if m := re.match(r"^(\w+)\s*=\s*(.*)$", command):
			local_vars[m.group(1)] = m.group(2)
			# print("set var:", m.group(1), '=', m.group(2))
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
		parser.add_argument('targets', metavar='target', type=str, nargs='+',
							help='list of targets to run')
		parser.add_argument('-o', '--output')
		args = parser.parse_args()

		# print("output:", args.output, ", targets:", args.targets)
		if args.output is not None:
			recording_file = open(args.output, 'a')

		groups = load_makefile('Makefile')
		for arg in args.targets:
			execute_makefile_commands(groups[arg])
		sys.exit(0)

	except KeyboardInterrupt:
		sys.exit(1)

if __name__ == '__main__':
	main()
