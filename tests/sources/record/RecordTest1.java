/**
 * Adapted from: https://docs.oracle.com/en/java/javase/17/language/records.html
 */
record /* Rectangle */ RecordTest1(double width, double height) {
    static double goldenRatio;

    static {
        goldenRatio = (1 + Math.sqrt(5)) / 2;
    }

    public static RecordTest1 createGoldenRect(double width) {
        return new RecordTest1(width, width * goldenRatio);
    }

    public double area() {
        return width * height;
    }
}
