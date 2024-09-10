#!/usr/bin/env python3

import os
import pty
import unittest
import subprocess
from unittest.mock import patch
from io import StringIO

class TestWeaselMake(unittest.TestCase):

	def test_echo_hello_world(self):
		"""Positive test case which echos hello world."""
		result = subprocess.run(['../weasel_make/weasel.py', 'hello'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
		self.assertIn("world!", result.stdout)
		self.assertEqual(result.returncode, 0)

	def test_command_group_dependency(self):
		"""Positive test case that executes a command group that depends on another makefile command group."""
		result = subprocess.run(['../weasel_make/weasel.py', 'subcommand'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
		self.assertIn("huh...", result.stdout)
		self.assertEqual(result.returncode, 0)

	def test_keep_output_in_console(self):
		"""Negative test that should be expected to keep the output in console rather than folding it."""
		result = subprocess.run(['../weasel_make/weasel.py', 'hello'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
		# The output should not contain control characters that fold the output
		self.assertNotIn("\033[", result.stdout)
		self.assertIn("world!", result.stdout)

	def test_many_command_erase_lines(self):
		"""Positive test case that verifies many_command prints the control string to erase lines."""
		# Create a pseudo-terminal to simulate a real terminal
		master, slave = pty.openpty()
		# Run the command with the slave end of the pty as the stdout and stderr
		result = subprocess.run(['../weasel_make/weasel.py', 'many_command'], stdout=slave, stderr=slave, text=True)
		# Close the slave to ensure we get EOF when reading from the master
		os.close(slave)
		# Read the output from the master end of the pty
		output = ""
		while True:
			try:
				chunk = os.read(master, 1024).decode('utf-8')
				if not chunk:  # EOF
					break
				output += chunk
			except OSError:
				# OSError is thrown on read if the slave end is closed, so we just break out of the loop
				break
		# Close the master end of the pty
		os.close(master)

		self.assertIn("\033[1A\033[K", output)
		self.assertEqual(result.returncode, 0)

	def test_bad_command_no_erase(self):
		"""Positive test case that verifies many_command prints the control string to erase lines."""
		# Create a pseudo-terminal to simulate a real terminal
		master, slave = pty.openpty()
		# Run the command with the slave end of the pty as the stdout and stderr
		result = subprocess.run(['../weasel_make/weasel.py', 'bad_command'], stdout=slave, stderr=slave, text=True)
		# Close the slave to ensure we get EOF when reading from the master
		os.close(slave)
		# Read the output from the master end of the pty
		output = ""
		while True:
			try:
				chunk = os.read(master, 1024).decode('utf-8')
				if not chunk:  # EOF
					break
				output += chunk
			except OSError:
				# OSError is thrown on read if the slave end is closed, so we just break out of the loop
				break
		# Close the master end of the pty
		os.close(master)

		self.assertNotIn("\033[1A\033[K", output)
		self.assertEqual(result.returncode, 1)

	def test_recursive_group_command(self):
		"""Positive test case that verifies recursive group command executed 5 times."""

		# Execute the recursive group command
		result = subprocess.run(['../weasel_make/weasel.py', 'recursive_group'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
		
		# Check if the output contains the expected string
		self.assertIn("Recursion step 5", result.stdout)
		self.assertEqual(result.returncode, 0)

	def test_custom_makefile(self):
		"""Positive test case that verifies using a custom makefile with the -f option."""
		# Create a temporary custom makefile
		custom_makefile_content = """
custom_target:
	echo "Custom makefile in action!"
"""
		with open('CustomMakefile', 'w') as f:
			f.write(custom_makefile_content)

		# Execute the command with the custom makefile
		result = subprocess.run(['../weasel_make/weasel.py', '-f', 'CustomMakefile', 'custom_target'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
		# Check if the output contains the expected string
		self.assertIn("Custom makefile in action!", result.stdout)
		self.assertEqual(result.returncode, 0)

		# Clean up
		os.remove('CustomMakefile')

	def test_target_not_found(self):
		"""Negative test case that verifies the error message when a target is not found."""
		result = subprocess.run(['../weasel_make/weasel.py', 'non_existent_target'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
		self.assertIn("Error: Target 'non_existent_target' not found in the makefile.", result.stderr)
		self.assertEqual(result.returncode, 1)


if __name__ == '__main__':
	os.chdir('test')
	unittest.main()
