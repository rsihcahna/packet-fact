import socket
import struct
import textwrap

def create_socket():
    try:
        s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.ntohs(3))
        return s
    except socket.error as e:
        print(f"Socket could not be created. Error Code: {str(e)}")
        return None

def capture_packets(sock):
    try:
        while True:
            raw_data, addr = sock.recvfrom(65536)
            eth_proto, data = ethernet_frame(raw_data)
            print('\nEthernet Frame:')
            print(f'\t- Protocol: {eth_proto}')
            
            # IPv4 packets
            if eth_proto == 8:
                version, header_length, ttl, proto, src, target, data = ipv4_packet(data)
                print('\t- IPv4 Packet:')
                print(f'\t\t- Version: {version}, Header Length: {header_length}, TTL: {ttl}')
                print(f'\t\t- Protocol: {proto}, Source: {src}, Target: {target}')
                
                # ICMP
                if proto == 1:
                    icmp_type, code, checksum, data = icmp_packet(data)
                    print('\t\t- ICMP Packet:')
                    print(f'\t\t\t- Type: {icmp_type}, Code: {code}, Checksum: {checksum}')
                    
                # TCP
                elif proto == 6:
                    src_port, dest_port, sequence, acknowledgment, flag_urg, flag_ack, flag_psh, flag_rst, flag_syn, flag_fin, data = tcp_segment(data)
                    print('\t\t- TCP Segment:')
                    print(f'\t\t\t- Source Port: {src_port}, Destination Port: {dest_port}')
                    print(f'\t\t\t- Sequence: {sequence}, Acknowledgment: {acknowledgment}')
                    print(f'\t\t\t- Flags:')
                    print(f'\t\t\t\t- URG: {flag_urg}, ACK: {flag_ack}, PSH: {flag_psh}, RST: {flag_rst}, SYN: {flag_syn}, FIN: {flag_fin}')
                    
                # UDP
                elif proto == 17:
                    src_port, dest_port, length, data = udp_segment(data)
                    print('\t\t- UDP Segment:')
                    print(f'\t\t\t- Source Port: {src_port}, Destination Port: {dest_port}, Length: {length}')
                    
                # Other
                else:
                    print(f'\t\t- Data:')
                    print(format_multi_line('\t\t\t', data))
    except KeyboardInterrupt:
        print("\nPacket capturing stopped.")
        sock.close()

def ethernet_frame(data):
    dest_mac, src_mac, proto = struct.unpack('! 6s 6s H', data[:14])
    return socket.htons(proto), data[14:]

def ipv4_packet(data):
    version_header_length = data[0]
    version = version_header_length >> 4
    header_length = (version_header_length & 15) * 4
    ttl, proto, src, target = struct.unpack('! 8x B B 2x 4s 4s', data[:20])
    return version, header_length, ttl, proto, ipv4(src), ipv4(target), data[header_length:]

def ipv4(addr):
    return '.'.join(map(str, addr))

def icmp_packet(data):
    icmp_type, code, checksum = struct.unpack('! B B H', data[:4])
    return icmp_type, code, checksum, data[4:]

def tcp_segment(data):
    (src_port, dest_port, sequence, acknowledgment, offset_reserved_flags) = struct.unpack('! H H L L H', data[:14])
    offset = (offset_reserved_flags >> 12) * 4
    flag_urg = (offset_reserved_flags & 32) >> 5
    flag_ack = (offset_reserved_flags & 16) >> 4
    flag_psh = (offset_reserved_flags & 8) >> 3
    flag_rst = (offset_reserved_flags & 4) >> 2
    flag_syn = (offset_reserved_flags & 2) >> 1
    flag_fin = offset_reserved_flags & 1
    return src_port, dest_port, sequence, acknowledgment, flag_urg, flag_ack, flag_psh, flag_rst, flag_syn, flag_fin, data[offset:]

def udp_segment(data):
    src_port, dest_port, size = struct.unpack('! H H 2x H', data[:8])
    return src_port, dest_port, size, data[8:]

def format_multi_line(prefix, string, size=80):
    size -= len(prefix)
    if isinstance(string, bytes):
        string = ''.join(r'\x{:02x}'.format(byte) for byte in string)
        if size % 2:
            size -= 1
    return '\n'.join([prefix + line for line in textwrap.wrap(string, size)])

def main():
    sock = create_socket()
    if sock:
        capture_packets(sock)

if __name__ == "__main__":
    main()
