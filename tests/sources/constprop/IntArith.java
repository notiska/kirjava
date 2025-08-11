/**
 * Integer arithmetic tests.
 */
public class IntArith {

    public static void main(final String[] args) {
        System.out.println(shortAdditions((short)5, (short)10));
    }

    private static int shortAdditions(final short a, final short b) {
        // TODO: Verify!!
        final int c = a + b;      // [-65536, 65534]
        final int d = c + 5;      // [-65531, 65539]
        final int e = d + 10 + c; // [-131057, 131083]
        return e - c;             // [-65521, 65549]
    }

}