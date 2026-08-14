import { Card } from "../../../components/ui/Card";
import type { ItineraryDay } from "../api/itineraryApi";

interface ItineraryWeatherCardProps {
  day: ItineraryDay;
}

type WeatherPresentation = {
  icon: string;
  label: string;
};

function getWeatherPresentation(condition: string): WeatherPresentation {
  const normalized = condition.trim().toLowerCase();

  if (!normalized) return { icon: "🌤️", label: "Weather unavailable" };
  if (/thunder|storm/.test(normalized)) return { icon: "⛈️", label: condition };
  if (/snow|sleet|ice/.test(normalized)) return { icon: "🌨️", label: condition };
  if (/rain|shower|drizzle/.test(normalized)) return { icon: "🌧️", label: condition };
  if (/cloud|overcast/.test(normalized)) return { icon: "☁️", label: condition };
  if (/clear|sunny/.test(normalized)) return { icon: "☀️", label: condition };
  if (/wind/.test(normalized)) return { icon: "🌬️", label: condition };
  if (/fog|mist/.test(normalized)) return { icon: "🌫️", label: condition };

  return { icon: "🌤️", label: condition };
}

function formatTemperature(value: number | null) {
  return value === null ? "—" : `${value}°F`;
}

export function ItineraryWeatherCard({ day }: ItineraryWeatherCardProps) {
  const hasWeather = Boolean(
    day.weather_condition ||
      day.weather_high_f !== null ||
      day.weather_low_f !== null ||
      day.weather_precipitation_chance !== null,
  );

  if (!hasWeather) {
    return (
      <Card className="border-dashed p-4" aria-label={`Weather for day ${day.day_number}`}>
        <p className="text-sm font-semibold">Weather</p>
        <p className="mt-1 text-sm text-neutral">Weather information is not available for this day yet.</p>
      </Card>
    );
  }

  const presentation = getWeatherPresentation(day.weather_condition);

  return (
    <Card className="border-info/30 bg-info/5 p-4" aria-label={`Weather for day ${day.day_number}`}>
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <span className="text-3xl" aria-hidden="true">{presentation.icon}</span>
          <div>
            <p className="text-sm font-semibold">Weather · Day {day.day_number}</p>
            <p className="mt-1 text-sm text-neutral">{presentation.label}</p>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-4 text-center text-sm">
          <div>
            <p className="text-xs text-neutral">High</p>
            <p className="mt-1 font-semibold">{formatTemperature(day.weather_high_f)}</p>
          </div>
          <div>
            <p className="text-xs text-neutral">Low</p>
            <p className="mt-1 font-semibold">{formatTemperature(day.weather_low_f)}</p>
          </div>
          <div>
            <p className="text-xs text-neutral">Precipitation</p>
            <p className="mt-1 font-semibold">
              {day.weather_precipitation_chance === null ? "—" : `${day.weather_precipitation_chance}%`}
            </p>
          </div>
        </div>
      </div>
    </Card>
  );
}
