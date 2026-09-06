import React, {
  useEffect,
  useState
} from 'react';

import {
  NavLink,
  Link,
  useLocation
} from 'react-router-dom';

import {
  ShieldAlert,
  MapPin,
  LayoutDashboard,
  Navigation
} from 'lucide-react';

import {
  getHabitations
} from '../api';

// ============================================================
// AASHRAY NAVBAR
// ============================================================
//
// Quick Jump now uses a REAL live village from the
// AASHRAY 1508-village dataset instead of the old mock:
//
// KL-WYD-000123 ❌
//
// ============================================================

export default function Navbar() {
  const location = useLocation();

  const [
    quickVillage,
    setQuickVillage
  ] = useState(null);

  // ----------------------------------------------------------
  // LOAD A REAL P1 VILLAGE FOR QUICK JUMP
  // ----------------------------------------------------------

  useEffect(() => {
    let mounted = true;

    async function loadQuickVillage() {
      try {
        const villages =
          await getHabitations();

        if (
          !mounted ||
          !Array.isArray(villages) ||
          villages.length === 0
        ) {
          return;
        }

        // Prefer a real P1 village.
        const p1Village =
          villages.find(
            (v) =>
              String(v?.priority)
                .toUpperCase() === 'P1'
          );

        // If no P1 is available, use the first
        // real village returned by the live API.
        const selectedVillage =
          p1Village ||
          villages[0];

        if (
          selectedVillage?.id
        ) {
          setQuickVillage(
            selectedVillage
          );
        }
      } catch (error) {
        console.error(
          'Navbar live village loading failed:',
          error
        );
      }
    }

    loadQuickVillage();

    return () => {
      mounted = false;
    };
  }, []);

  // ----------------------------------------------------------
  // REAL VILLAGE ID
  // ----------------------------------------------------------

  const villageId =
    quickVillage?.id || null;

  // ----------------------------------------------------------
  // PRIMARY NAVIGATION STYLE
  // ----------------------------------------------------------

  const navClass = ({
    isActive
  }) =>
    `flex items-center gap-2 px-4 py-2 rounded-lg text-xs sm:text-sm font-bold transition ${
      isActive
        ? 'bg-blue-600 text-white shadow-sm'
        : 'text-slate-300 hover:bg-slate-800 hover:text-white'
    }`;

  // ----------------------------------------------------------
  // QUICK JUMP STYLE
  // ----------------------------------------------------------

  const quickLinkClass =
    'px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition';

  return (
    <header className="bg-[#0b192c] text-white shadow-lg sticky top-0 z-50 border-b border-slate-700/60">

      {/* ======================================================
          TOP GOVERNMENT STYLE SUB-HEADER
      ====================================================== */}

      <div className="bg-[#060e18] px-4 py-1 text-xs text-slate-400 border-b border-slate-800 flex flex-wrap justify-between items-center gap-2">

        <div className="flex items-center gap-2">

          <span className="inline-block w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>

          <span className="truncate">
            National Climate Resilient Relocation & Disaster Risk Decision Support System
          </span>

        </div>

        <div className="flex items-center gap-3 text-[11px] font-mono">

          <span className="bg-amber-400/20 text-amber-300 border border-amber-400/40 px-2 py-0.5 rounded font-bold">
            AASHRAY - National Climate Resilience Platform
          </span>

          <span className="hidden sm:inline text-slate-500">
            NDMA-KSDMA
          </span>

        </div>

      </div>

      {/* ======================================================
          MAIN NAVBAR
      ====================================================== */}

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">

        <div className="flex items-center justify-between h-16">

          {/* --------------------------------------------------
              LOGO / BRAND
          -------------------------------------------------- */}

          <div className="flex items-center gap-3">

            <Link
              to="/"
              className="flex items-center gap-3 group"
            >

              <div className="w-10 h-10 rounded-xl bg-blue-600/30 border border-blue-500/40 flex items-center justify-center text-blue-400 group-hover:bg-blue-600/50 transition">

                <ShieldAlert className="w-6 h-6 text-blue-400" />

              </div>

              <div>

                <div className="flex items-center gap-2">

                  <span className="font-extrabold text-lg tracking-wider text-white">
                    AASHRAY
                  </span>

                  <span className="text-[10px] uppercase font-bold tracking-widest bg-blue-900/80 text-blue-300 border border-blue-700/50 px-1.5 py-0.5 rounded">
                    Official Portal
                  </span>

                </div>

                <p className="text-[11px] text-slate-400 tracking-tight">
                  Disaster Risk & Resettlement Engine
                </p>

              </div>

            </Link>

          </div>

          {/* --------------------------------------------------
              PRIMARY NAVIGATION
          -------------------------------------------------- */}

          <nav className="flex items-center gap-2">

            <NavLink
              to="/"
              end
              className={navClass}
            >

              <LayoutDashboard className="w-4 h-4" />

              <span>
                Dashboard
              </span>

            </NavLink>

            <NavLink
              to="/map"
              className={navClass}
            >

              <MapPin className="w-4 h-4" />

              <span>
                Map View
              </span>

            </NavLink>

          </nav>

        </div>

      </div>

      {/* ======================================================
          QUICK ROUTE NAVIGATOR
      ====================================================== */}

      <div className="bg-[#10233b] border-t border-slate-800/80 px-4 py-1.5 text-xs text-slate-300">

        <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-2">

          {/* --------------------------------------------------
              ACTIVE ROUTE
          -------------------------------------------------- */}

          <div className="flex items-center gap-2">

            <Navigation className="w-3.5 h-3.5 text-blue-400" />

            <span className="text-slate-400 font-semibold uppercase tracking-wider text-[11px]">
              Active Route:
            </span>

            <code className="bg-slate-900/90 text-amber-300 px-2 py-0.5 rounded font-mono text-[11px] border border-slate-700">
              {location.pathname}
            </code>

          </div>

          {/* --------------------------------------------------
              QUICK JUMP
          -------------------------------------------------- */}

          <div className="flex items-center gap-1.5 text-[11px]">

            <span className="text-slate-400 hidden md:inline">
              Quick Jump:
            </span>

            {villageId ? (
              <>
                {/* ------------------------------------------
                    REAL P1 HABITATION
                ------------------------------------------ */}

                <Link
                  to={`/habitation/${encodeURIComponent(
                    villageId
                  )}`}
                  className={quickLinkClass}
                >
                  P1 Habitation
                </Link>

                {/* ------------------------------------------
                    REAL RELOCATION
                ------------------------------------------ */}

                <Link
                  to={`/habitation/${encodeURIComponent(
                    villageId
                  )}/relocation`}
                  className={quickLinkClass}
                >
                  Relocation
                </Link>

                {/* ------------------------------------------
                    REAL WHAT-IF
                ------------------------------------------ */}

                <Link
                  to={`/habitation/${encodeURIComponent(
                    villageId
                  )}/whatif`}
                  className={quickLinkClass}
                >
                  What-If
                </Link>

                {/* ------------------------------------------
                    REAL RECOMMENDATION
                ------------------------------------------ */}

                <Link
                  to={`/recommendation/${encodeURIComponent(
                    villageId
                  )}`}
                  className={quickLinkClass}
                >
                  Recommendation
                </Link>
              </>
            ) : (
              /* --------------------------------------------
                 LIVE API LOADING STATE
              -------------------------------------------- */

              <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-500 border border-slate-700">
                Loading live village...
              </span>
            )}

          </div>

        </div>

      </div>

    </header>
  );
}