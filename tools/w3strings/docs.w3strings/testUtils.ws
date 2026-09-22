function test_log(msg : string, optional hudOut : bool) {
    if (hudOut) GetWitcherPlayer().DisplayHudMessage("[TESTING] " + msg);
    LogChannel('TESTING', msg);
}

function assertTrue(condition : bool, optional msg : string, optional hudOut: bool) : bool {
    if (!condition) {
        test_log("ASSERT FAILED: " + msg, hudOut);
    } else {
        test_log("ASSERT OK: " + msg);
    }
    return condition;
}

function logTestResult(testName: string, failed: int, optional hudOut: bool) {
    if (failed == 0) {
        test_log(testName + ": SUCCESS", hudOut);
    } else {
        test_log(testName + ": " + failed + " FAILED", hudOut);
    }
}
