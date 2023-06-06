import json
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import socket

def update_plot(data):
    # Extract the necessary data for plotting
    coordinates = []
    for btr in data['fram']['btrs']:
        coordinates.append(btr['tran'])

    # Convert the coordinates to separate lists for x, y, z axes
    x = [coord[0] for coord in coordinates]
    y = [coord[1] for coord in coordinates]
    z = [coord[2] for coord in coordinates]

    # Plot the human frame
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.scatter(x, y, z)
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    plt.show()

# Create a socket object
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Define the server address and port
server_address = ('10.18.80.194', 39540)

# Connect to the server
sock.connect(server_address)

try:
    while True:
        # Receive data from the server
        data = sock.recv(1024).decode('utf-8')
        if not data:
            break

        # Parse the JSON-formatted data
        json_data = json.loads(data)

        # Update the plot
        update_plot(json_data)

finally:
    # Close the socket connection
    sock.close()
