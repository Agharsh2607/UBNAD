from bcc import BPF
import socket
import struct

bpf = BPF(src_file="ebpf/net_monitor.c")
bpf.attach_kprobe(event="tcp_v4_connect", fn_name="trace_connect")

def ip_to_str(ip):
    return socket.inet_ntoa(struct.pack("I", ip))

def print_event(cpu, data, size):
    event = bpf["events"].event(data)
    print({
        "pid": event.pid,
        "process": event.comm.decode(),
        "dest_ip": ip_to_str(event.daddr),
        "port": event.dport
    })

bpf["events"].open_perf_buffer(print_event)

while True:
    bpf.perf_buffer_poll()
