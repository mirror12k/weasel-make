from setuptools import setup, find_packages
from setuptools.command.install import install
import os

class CustomInstallCommand(install):
    """Customized setuptools install command to install bash completions."""
    def run(self):
        # Call the standard setuptools install command
        install.run(self)

        # Install the bash completion script
        bash_completion_dir = os.path.expanduser('/etc/bash_completion.d')
        weasel_completion_script = 'weasel_autocomplete.sh'
        try:
            self.copy_file(weasel_completion_script, bash_completion_dir)
        except:
            bash_completion_dir = os.path.expanduser('~/.bash_completion.d')
            weasel_completion_script = 'weasel_autocomplete.sh'
            self.copy_file(weasel_completion_script, bash_completion_dir)

        try:
            # Try to Append the source command to the system-wide bashrc
            self.append_to_bashrc(bash_completion_dir, weasel_completion_script, bashrc_path='/etc/bash.bashrc')
        except:
            # Append the source command to the user's .bashrc
            self.append_to_bashrc(bash_completion_dir, weasel_completion_script)

    def copy_file(self, file_path, destination):
        # This function copies the autocomplete script to the specified directory
        import shutil
        os.makedirs(destination, exist_ok=True)
        shutil.copy(file_path, destination)
        print(f"Installed bash completions at {destination}/{file_path}")

    def append_to_bashrc(self, bash_completion_dir, script_name, bashrc_path='~/.bashrc'):
        # This function appends the source command to the user's .bashrc
        bashrc_path = os.path.expanduser(bashrc_path)
        source_command = f'\n\nsource {bash_completion_dir}/{script_name}\n\n'

        # Check if the source command is already in .bashrc
        if os.path.exists(bashrc_path):
            with open(bashrc_path, 'r+') as bashrc:
                lines = bashrc.readlines()
                if source_command not in lines:
                    bashrc.write(source_command)
                    print(f"Appended source command to {bashrc_path}")
        else:
            with open(bashrc_path, 'w') as bashrc:
                bashrc.write(source_command)
                print(f"Created {bashrc_path} and appended source command")

setup(
   name='weasel-make',
   version='0.1.1',
   packages=find_packages(),
   install_requires=[],
   entry_points={
       'console_scripts': [
           'weasel=weasel_make.weasel:main',
       ],
   },
   cmdclass={
       'install': CustomInstallCommand,
   },
   # Metadata
   author='Mirror12k',
   description='A Makefile-compatibile Build Tool',
   long_description=open('README.md').read(),
   long_description_content_type='text/markdown',
   license='MIT',
   keywords='make build-tool weasel makefile',
   url='https://github.com/mirror12k/weasel-make',
   include_package_data=True,
   classifiers=[
       'Programming Language :: Python :: 3',
       'License :: OSI Approved :: MIT License',
   ],
)
