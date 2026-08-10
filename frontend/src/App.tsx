import { Route, Routes } from "react-router-dom";
import { HomePage } from "./features/home/pages/HomePage";
import { ProtectedRoute } from "./routes/ProtectedRoute";
import { routes } from "./routes/routeConfig";

function PlaceholderPage({ title }: { title: string }) {
  return <main className="placeholder-page"><h1>{title}</h1><p>This route is wired as an empty application shell. Its feature chapter comes later.</p></main>;
}

export default function App() {
  return (
    <Routes>
      <Route path={routes.public.landing} element={<HomePage />} />
      <Route path={routes.public.login} element={<PlaceholderPage title="Login" />} />
      <Route path={routes.public.register} element={<PlaceholderPage title="Register" />} />
      <Route path={routes.public.sharedItinerary} element={<PlaceholderPage title="Shared Itinerary" />} />
      <Route element={<ProtectedRoute />}>
        <Route path={routes.protected.dashboard} element={<PlaceholderPage title="Dashboard" />} />
        <Route path={routes.protected.createTrip} element={<PlaceholderPage title="Create Trip" />} />
        <Route path={routes.protected.tripDetail} element={<PlaceholderPage title="Trip Detail" />} />
        <Route path={routes.protected.itinerary} element={<PlaceholderPage title="Itinerary" />} />
        <Route path={routes.protected.budget} element={<PlaceholderPage title="Budget" />} />
        <Route path={routes.protected.recommendations} element={<PlaceholderPage title="Recommendations" />} />
        <Route path={routes.protected.packing} element={<PlaceholderPage title="Packing" />} />
        <Route path={routes.protected.chat} element={<PlaceholderPage title="Chat" />} />
        <Route path={routes.protected.profile} element={<PlaceholderPage title="Profile" />} />
        <Route path={routes.protected.settings} element={<PlaceholderPage title="Settings" />} />
        <Route path={routes.protected.bookings} element={<PlaceholderPage title="Bookings" />} />
        <Route path={routes.protected.analyticsAdmin} element={<PlaceholderPage title="Analytics" />} />
      </Route>
      <Route path="*" element={<HomePage />} />
    </Routes>
  );
}