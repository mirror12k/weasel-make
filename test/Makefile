
many_command:
many_command:
many_command:
	echo "many times!"
hello:
	echo "world!" && sleep 1
	echo "wat!"
empty_command:


many_command:
subcommand: another_command
another_command:
	echo "huh..."
bad_command:
	false
	echo "nope..."


recursive_group: step1
step1: step2
step2: step3
step3: step4
step4: step5
step5:
	echo "Recursion step 5"

bashscript:
	./test/scripttest.sh
