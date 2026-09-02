package com.aashray.controller;

import java.util.List;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.aashray.dto.dashboard.DashboardHotspotDto;
import com.aashray.dto.dashboard.DashboardSummaryDto;
import com.aashray.service.DashboardService;

@RestController
@RequestMapping("/api/v1/dashboard")
public class DashboardController {

    private final DashboardService dashboardService;

    public DashboardController(DashboardService dashboardService) {
        this.dashboardService = dashboardService;
    }

    @GetMapping("/summary")
    public DashboardSummaryDto getSummary(@RequestParam(required = false) String region) {
        return dashboardService.getSummary(region);
    }

    @GetMapping("/hotspots")
    public List<DashboardHotspotDto> getHotspots(@RequestParam(required = false) String region,
                                                 @RequestParam(defaultValue = "10") int limit) {
        return dashboardService.getHotspots(region, limit);
    }
}
