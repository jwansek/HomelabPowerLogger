import snmpOmada
import mikrotik

if __name__ == "__main__":
    points = snmpOmada.get_points() + mikrotik.get_points()
    print(points)
    mikrotik.append(points)