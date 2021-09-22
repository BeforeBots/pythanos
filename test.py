from pythanos.snap import Snap

obj = Snap(r"...")

# for i in range(10000+1):
#     obj.progbar(i, 10000, "yoyo")

# obj = Snap("")
# print(obj.get_nth_dirs(r"...", n=3))

obj.group_by_exts(exts=['pdf', 'jpg'])
