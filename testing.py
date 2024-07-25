import highlighting_hyperlinks as hh

num_of_texts = 10
n = 0
not_good = True

while not_good == True:
    for i in range(num_of_texts):
        input_name = "texts/test_text_" + str(i + 1)
        output_name = "texts/outputs/test_output_" + str(i + 1)
        hh.get_hyperlinks(input_name, output_name)
        print("\n[+] \033[1m" + str(i + 1) + " текст прогнан \033[0m[+]\n")
    n += 1
    ans = input("Еще раз? any/N")
    if ans == "N" or ans == "n":
        not_good = False
    else:
        continue

print("Потребовалось " + str(n) + " попытки(-ок)")
