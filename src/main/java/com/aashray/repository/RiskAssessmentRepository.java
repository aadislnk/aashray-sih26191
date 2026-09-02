package com.aashray.repository;

import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.util.List;
import java.util.UUID;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import com.aashray.entity.RiskAssessment;

public interface RiskAssessmentRepository extends JpaRepository<RiskAssessment, UUID> {

    @Query(value = """
        with latest_risk as (
            select *
            from (
                select ra.*,
                       row_number() over (
                           partition by ra.habitation_id
                           order by ra.assessment_time desc, ra.id desc
                       ) as row_number
                from risk_assessment ra
            ) ranked_risk
            where ranked_risk.row_number = 1
        )
        select coalesce(sum(case when lr.priority = 'P1' then 1 else 0 end), 0) as "p1Count",
               coalesce(sum(case when lr.priority = 'P2' then 1 else 0 end), 0) as "p2Count",
               coalesce(sum(case when lr.priority = 'P3' then 1 else 0 end), 0) as "p3Count",
               coalesce(sum(case when lr.priority = 'P4' then 1 else 0 end), 0) as "p4Count",
               count(h.id) as "totalHabitations",
               max(lr.assessment_time) as "lastUpdated"
        from habitation h
        left join latest_risk lr on lr.habitation_id = h.id
        """, nativeQuery = true)
    DashboardSummaryProjection summarizeLatestRisk();

    @Query(value = """
        with latest_risk as (
            select *
            from (
                select ra.*,
                       row_number() over (
                           partition by ra.habitation_id
                           order by ra.assessment_time desc, ra.id desc
                       ) as row_number
                from risk_assessment ra
            ) ranked_risk
            where ranked_risk.row_number = 1
        )
        select coalesce(sum(case when lr.priority = 'P1' then 1 else 0 end), 0) as "p1Count",
               coalesce(sum(case when lr.priority = 'P2' then 1 else 0 end), 0) as "p2Count",
               coalesce(sum(case when lr.priority = 'P3' then 1 else 0 end), 0) as "p3Count",
               coalesce(sum(case when lr.priority = 'P4' then 1 else 0 end), 0) as "p4Count",
               count(h.id) as "totalHabitations",
               max(lr.assessment_time) as "lastUpdated"
        from habitation h
        join admin_boundary ab on ab.id = h.admin_boundary_id
        left join latest_risk lr on lr.habitation_id = h.id
        where ab.name = :region
        """, nativeQuery = true)
    DashboardSummaryProjection summarizeLatestRiskByRegion(@Param("region") String region);

    @Query(value = """
        select cast(h.id as varchar) as "habitationId",
               h.name as "habitationName",
               lr.priority as "priority",
               lr.risk_score as "riskScore",
               ST_AsGeoJSON(h.geometry)::text as "geometry",
               lr.assessment_time as "assessmentTime"
        from (
            select *
            from (
                select ra.*,
                       row_number() over (
                           partition by ra.habitation_id
                           order by ra.assessment_time desc, ra.id desc
                       ) as row_number
                from risk_assessment ra
            ) ranked_risk
            where ranked_risk.row_number = 1
        ) lr
        join habitation h on h.id = lr.habitation_id
        order by case lr.priority
                    when 'P1' then 1
                    when 'P2' then 2
                    when 'P3' then 3
                    when 'P4' then 4
                    else 5
                 end,
                 lr.risk_score desc,
                 lr.assessment_time desc,
                 h.id
        limit :limit
        """, nativeQuery = true)
    List<DashboardHotspotProjection> findTopHotspots(@Param("limit") int limit);

    @Query(value = """
        select cast(h.id as varchar) as "habitationId",
               h.name as "habitationName",
               lr.priority as "priority",
               lr.risk_score as "riskScore",
               ST_AsGeoJSON(h.geometry)::text as "geometry",
               lr.assessment_time as "assessmentTime"
        from (
            select *
            from (
                select ra.*,
                       row_number() over (
                           partition by ra.habitation_id
                           order by ra.assessment_time desc, ra.id desc
                       ) as row_number
                from risk_assessment ra
            ) ranked_risk
            where ranked_risk.row_number = 1
        ) lr
        join habitation h on h.id = lr.habitation_id
        join admin_boundary ab on ab.id = h.admin_boundary_id
        where ab.name = :region
        order by case lr.priority
                    when 'P1' then 1
                    when 'P2' then 2
                    when 'P3' then 3
                    when 'P4' then 4
                    else 5
                 end,
                 lr.risk_score desc,
                 lr.assessment_time desc,
                 h.id
        limit :limit
        """, nativeQuery = true)
    List<DashboardHotspotProjection> findTopHotspotsByRegion(@Param("region") String region,
                                                             @Param("limit") int limit);

    interface DashboardSummaryProjection {
        Long getP1Count();
        Long getP2Count();
        Long getP3Count();
        Long getP4Count();
        Long getTotalHabitations();
        OffsetDateTime getLastUpdated();
    }

    interface DashboardHotspotProjection {
        String getHabitationId();
        String getHabitationName();
        String getPriority();
        BigDecimal getRiskScore();
        String getGeometry();
        OffsetDateTime getAssessmentTime();
    }
}
