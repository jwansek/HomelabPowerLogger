import snmpOmada
import mikrotik

if __name__ == "__main__":
    points = snmpOmada.get_points() + mikrotik.get_points()
    mikrotik.print_points(points)
    mikrotik.append(points)