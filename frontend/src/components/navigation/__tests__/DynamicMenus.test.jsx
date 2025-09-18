/**
 * Testes para o sistema de menus dinâmicos
 */

import React from "react";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { DynamicSidebar } from "../DynamicSidebar";
import { MenuItem } from "../MenuItem";

// Mock da API
jest.mock("../../../services/api", () => ({
  get: jest.fn(),
}));

// Mock dos hooks
jest.mock("../../../hooks/useDynamicMenus", () => ({
  useDynamicMenus: () => ({
    menus: mockMenus,
    loading: false,
    error: null,
    refreshMenus: jest.fn(),
    isRoot: false,
    userInfo: { name: "Test User", email: "test@test.com" },
    context: { type: "establishment", name: "Test Establishment" },
    lastFetch: "12:00:00",
    cacheAge: 30,
  }),
}));

const mockMenus = [
  {
    id: 1,
    name: "Dashboard",
    slug: "dashboard",
    url: "/admin/dashboard",
    icon: "LayoutDashboard",
    level: 0,
    sort_order: 1,
    children: [],
  },
  {
    id: 10,
    name: "Home Care",
    slug: "home-care",
    url: null,
    icon: "Heart",
    level: 0,
    sort_order: 10,
    badge_text: "Pro",
    badge_color: "bg-purple-500",
    children: [
      {
        id: 11,
        name: "Pacientes",
        slug: "pacientes",
        url: "/admin/patients",
        icon: "Activity",
        level: 1,
        sort_order: 1,
        children: [],
      },
    ],
  },
];

const renderWithRouter = (component) => {
  return render(<BrowserRouter>{component}</BrowserRouter>);
};

describe("DynamicSidebar", () => {
  test("renderiza corretamente", () => {
    renderWithRouter(<DynamicSidebar />);

    expect(screen.getByText("Pro Team Care")).toBeInTheDocument();
    expect(screen.getByText("Dashboard")).toBeInTheDocument();
    expect(screen.getByText("Home Care")).toBeInTheDocument();
  });

  test("renderiza no modo colapsado", () => {
    renderWithRouter(<DynamicSidebar collapsed={true} />);

    // No modo colapsado, o texto não deve aparecer
    expect(screen.queryByText("Pro Team Care")).not.toBeInTheDocument();
  });

  test("renderiza badges corretamente", () => {
    renderWithRouter(<DynamicSidebar />);

    expect(screen.getByText("Pro")).toBeInTheDocument();
  });
});

describe("MenuItem", () => {
  const mockMenu = {
    id: 1,
    name: "Test Menu",
    slug: "test-menu",
    url: "/test",
    icon: "Settings",
    level: 0,
    children: [],
  };

  test("renderiza menu sem filhos", () => {
    renderWithRouter(<MenuItem menu={mockMenu} />);

    expect(screen.getByText("Test Menu")).toBeInTheDocument();
  });

  test("renderiza menu com filhos", () => {
    const menuWithChildren = {
      ...mockMenu,
      children: [
        {
          id: 2,
          name: "Submenu",
          slug: "submenu",
          url: "/test/submenu",
          icon: "SubIcon",
          level: 1,
          children: [],
        },
      ],
    };

    renderWithRouter(<MenuItem menu={menuWithChildren} />);

    expect(screen.getByText("Test Menu")).toBeInTheDocument();

    // Click para expandir
    const menuItem = screen.getByText("Test Menu").closest("div");
    fireEvent.click(menuItem);

    // Submenu deve aparecer
    expect(screen.getByText("Submenu")).toBeInTheDocument();
  });

  test("renderiza no modo colapsado", () => {
    renderWithRouter(<MenuItem menu={mockMenu} collapsed={true} />);

    // Texto não deve aparecer no modo colapsado
    expect(screen.queryByText("Test Menu")).not.toBeInTheDocument();
  });
});

describe("Integração do Sistema", () => {
  test("hierarquia de menus funciona corretamente", () => {
    const { container } = renderWithRouter(<DynamicSidebar />);

    // Verificar estrutura hierárquica
    const homeCaremenu = screen.getByText("Home Care").closest("div");
    fireEvent.click(homeCaremenu);

    // Submenu deve aparecer
    expect(screen.getByText("Pacientes")).toBeInTheDocument();
  });
});

export {};
