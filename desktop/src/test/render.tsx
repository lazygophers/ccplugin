import { render } from "@testing-library/react";
import {
  createMemoryRouter,
  RouterProvider,
  type RouteObject,
} from "react-router-dom";

export function renderWithRouter(
  routes: RouteObject[],
  opts?: { initialEntries?: string[] }
) {
  const router = createMemoryRouter(routes, {
    initialEntries: opts?.initialEntries ?? ["/"],
  });
  return {
    router,
    ...render(<RouterProvider router={router} />),
  };
}
