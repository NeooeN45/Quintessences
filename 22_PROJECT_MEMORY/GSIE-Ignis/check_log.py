import pyulog
import sys

ulog_path = sys.argv[1]
ulog = pyulog.ULog(ulog_path)
for topic in ulog.data_list:
    name = topic.name.lower()
    if 'actuator' in name or 'motor' in name or 'thrust' in name or 'control' in name:
        print(f"Topic: {topic.name}")
        for field in topic.data.keys():
            if field != 'timestamp':
                vals = topic.data[field]
                nonzero = vals[vals != 0]
                print(f"  {field}: min={vals.min():.4f} max={vals.max():.4f} nonzero={len(nonzero)}/{len(vals)}")
