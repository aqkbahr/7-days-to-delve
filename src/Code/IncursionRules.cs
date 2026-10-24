using System;

namespace Delve
{
    // Pure rules shared by the game controller and regression tests.
    public static class IncursionRules
    {
        public static bool ArrivalWindow(bool bloodMoon, bool daytime, int hour, int dawn)
        {
            int remaining = (dawn - hour + 24) % 24;
            return bloodMoon && !daytime && remaining > 0 && remaining <= 2;
        }

        // Identify the night by the day on which it ENDS, including before midnight.
        public static int NightId(int day, int hour, int dawn)
        { return hour >= dawn ? day + 1 : day; }

        public static int BossHealth(int participants)
        { return 900 + 450 * (Math.Max(1, Math.Min(8, participants)) - 1); }

        // 4 seconds warning, 6 seconds assault, 6 seconds recovery, 14 normal.
        public static int Phase(float elapsed)
        {
            if (elapsed < 12) return 0;
            float cycle = (elapsed - 12) % 30;
            return cycle < 4 ? 1 : cycle < 10 ? 2 : cycle < 16 ? 3 : 0;
        }
    }
}
