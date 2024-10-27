from enum import Enum
from typing import List

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.db.models.affiliations import affiliations_table
from app.db.session import Base

RELATORS_BASE_URL = "https://id.loc.gov/vocabulary/relators/"


class Contribution(Base):
    """
    Model for persistence of contributions
    """

    class LOCAuthorRoles(Enum):
        """
        Enum class for Library of Congress (LOC) relators
        """

        ACT = ("Actor", f"{RELATORS_BASE_URL}act.html")
        ADP = ("Adapter", f"{RELATORS_BASE_URL}adp.html")
        ANM = ("Animator", f"{RELATORS_BASE_URL}anm.html")
        ANT = ("Bibliographic antecedent", f"{RELATORS_BASE_URL}ant.html")
        ANN = ("Annotator", f"{RELATORS_BASE_URL}ann.html")
        ANL = ("Analyst", f"{RELATORS_BASE_URL}anl.html")
        ARR = ("Arranger", f"{RELATORS_BASE_URL}arr.html")
        ART = ("Artist", f"{RELATORS_BASE_URL}art.html")
        ARD = ("Artistic Director", f"{RELATORS_BASE_URL}ard.html")
        ASG = ("Assignee", f"{RELATORS_BASE_URL}asg.html")
        ASN = ("Associated name", f"{RELATORS_BASE_URL}asn.html")
        AUC = ("Auctioneer", f"{RELATORS_BASE_URL}auc.html")
        AUT = ("Author", f"{RELATORS_BASE_URL}aut.html")
        AQT = ("Author in quotations or text abstracts", f"{RELATORS_BASE_URL}aqt.html")
        AFT = ("Author of afterword, colophon, etc.", f"{RELATORS_BASE_URL}aft.html")
        AUI = ("Author of introduction, etc.", f"{RELATORS_BASE_URL}aui.html")
        AUS = ("Screenwriter", f"{RELATORS_BASE_URL}aus.html")
        BND = ("Binder", f"{RELATORS_BASE_URL}bnd.html")
        BDD = ("Binding designer", f"{RELATORS_BASE_URL}bdd.html")
        BKD = ("Book designer", f"{RELATORS_BASE_URL}bkd.html")
        BPD = ("Bookplate producer", f"{RELATORS_BASE_URL}bpd.html")
        BJD = ("Bookjacket designer", f"{RELATORS_BASE_URL}bjd.html")
        BSL = ("Bookseller", f"{RELATORS_BASE_URL}bsl.html")
        CLL = ("Calligrapher", f"{RELATORS_BASE_URL}cll.html")
        CTG = ("Cartographer", f"{RELATORS_BASE_URL}ctg.html")
        CNS = ("Censor", f"{RELATORS_BASE_URL}cns.html")
        CHR = ("Choreographer", f"{RELATORS_BASE_URL}chr.html")
        CLB = ("Collaborator", "discontinued code")
        COL = ("Collector", f"{RELATORS_BASE_URL}col.html")
        CMM = ("Commentator", f"{RELATORS_BASE_URL}cmm.html")
        CMT = ("Compositor", f"{RELATORS_BASE_URL}cmt.html")
        CWT = ("Commentator for written text", f"{RELATORS_BASE_URL}cwt.html")
        COM = ("Compiler", f"{RELATORS_BASE_URL}com.html")
        CMP = ("Composer", f"{RELATORS_BASE_URL}cmp.html")
        CCP = ("Conceptor", f"{RELATORS_BASE_URL}ccp.html")
        CND = ("Conductor", f"{RELATORS_BASE_URL}cnd.html")
        CSP = ("Consultant to a project", f"{RELATORS_BASE_URL}csp.html")
        CTB = ("Contributor", f"{RELATORS_BASE_URL}ctb.html")
        CPH = ("Copyright holder", f"{RELATORS_BASE_URL}cph.html")
        CRR = ("Corrector", f"{RELATORS_BASE_URL}crr.html")
        CUR = ("Curator", f"{RELATORS_BASE_URL}cur.html")
        DNC = ("Dancer", f"{RELATORS_BASE_URL}dnc.html")
        DTE = ("Dedicatee", f"{RELATORS_BASE_URL}dte.html")
        DTO = ("Dedicator", f"{RELATORS_BASE_URL}dto.html")
        DGC = ("Degree committee member", f"{RELATORS_BASE_URL}dgc.html")
        DGG = ("Degree granting institution", f"{RELATORS_BASE_URL}dgg.html")
        DIS = ("Dissertant", f"{RELATORS_BASE_URL}dis.html")
        DRT = ("Director", f"{RELATORS_BASE_URL}drt.html")
        DST = ("Distributor", f"{RELATORS_BASE_URL}dst.html")
        DNR = ("Donor", f"{RELATORS_BASE_URL}dnr.html")
        DUB = ("Dubious author", f"{RELATORS_BASE_URL}dub.html")
        EDC = ("Editor of compilation", f"{RELATORS_BASE_URL}edc.html")
        EDT = ("Editor", f"{RELATORS_BASE_URL}edt.html")
        EGR = ("Engraver", f"{RELATORS_BASE_URL}egr.html")
        ETR = ("Etcher", f"{RELATORS_BASE_URL}etr.html")
        EXP = ("Expert", f"{RELATORS_BASE_URL}exp.html")
        FMD = ("Film director", f"{RELATORS_BASE_URL}fmd.html")
        FLM = ("Film editor", f"{RELATORS_BASE_URL}flm.html")
        FRG = ("Forger", f"{RELATORS_BASE_URL}frg.html")
        FMO = ("Former owner", f"{RELATORS_BASE_URL}fmo.html")
        GRT = ("Graphic technician", "Discontinued code")
        HNR = ("Honoree", f"{RELATORS_BASE_URL}hnr.html")
        ILU = ("Illuminator", f"{RELATORS_BASE_URL}ilu.html")
        ILL = ("Illustrator", f"{RELATORS_BASE_URL}ill.html")
        INS = ("Inscriber", f"{RELATORS_BASE_URL}ins.html")
        IVE = ("Interviewee", f"{RELATORS_BASE_URL}ive.html")
        IVR = ("Interviewer", f"{RELATORS_BASE_URL}ivr.html")
        INV = ("Inventor", f"{RELATORS_BASE_URL}inv.html")
        ISB = ("Issuing body", f"{RELATORS_BASE_URL}isb.html")
        LBT = ("Librettist", f"{RELATORS_BASE_URL}lbt.html")
        LSE = ("Licensee", f"{RELATORS_BASE_URL}lse.html")
        LSO = ("Licensor", f"{RELATORS_BASE_URL}lso.html")
        LTG = ("Lithographer", f"{RELATORS_BASE_URL}ltg.html")
        LYR = ("Lyricist", f"{RELATORS_BASE_URL}lyr.html")
        MTE = ("Metal-engraver", f"{RELATORS_BASE_URL}mte.html")
        MON = ("Monitor", f"{RELATORS_BASE_URL}mon.html")
        MUS = ("Musician", f"{RELATORS_BASE_URL}mus.html")
        NRT = ("Narrator", f"{RELATORS_BASE_URL}nrt.html")
        OSP = ("Onscreen presenter", f"{RELATORS_BASE_URL}osp.html")
        OPN = ("Opponent", f"{RELATORS_BASE_URL}opn.html")
        ORM = ("Organizer", f"{RELATORS_BASE_URL}orm.html")
        ORG = ("Originator", f"{RELATORS_BASE_URL}org.html")
        OTH = ("Other", f"{RELATORS_BASE_URL}oth.html")
        PPM = ("Papermaker", f"{RELATORS_BASE_URL}ppm.html")
        POP = ("Printer of plate", f"{RELATORS_BASE_URL}pop.html")
        PTH = ("Patent holder", f"{RELATORS_BASE_URL}pth.html")
        PRF = ("Performer", f"{RELATORS_BASE_URL}prf.html")
        PHT = ("Photographer", f"{RELATORS_BASE_URL}pht.html")
        PRA = ("Praeses", f"{RELATORS_BASE_URL}pra.html")
        PRT = ("Printer", f"{RELATORS_BASE_URL}prt.html")
        PRO = ("Producer", f"{RELATORS_BASE_URL}pro.html")
        PRD = ("Production personnel", f"{RELATORS_BASE_URL}prd.html")
        PRG = ("Programmer", f"{RELATORS_BASE_URL}prg.html")
        PDR = ("Project director", f"{RELATORS_BASE_URL}pdr.html")
        PFR = ("Proofreader", f"{RELATORS_BASE_URL}pfr.html")
        PBL = ("Publisher", f"{RELATORS_BASE_URL}pbl.html")
        PBD = ("Publisher director", f"{RELATORS_BASE_URL}pbd.html")
        PPT = ("Puppeteer", f"{RELATORS_BASE_URL}ppt.html")
        RAP = ("Rapporteur", f"{RELATORS_BASE_URL}rap.html")
        RCP = ("Addressee", f"{RELATORS_BASE_URL}rcp.html")
        RCE = ("Recording engineer", f"{RELATORS_BASE_URL}rce.html")
        RTH = ("Research team head", f"{RELATORS_BASE_URL}rth.html")
        RTM = ("Research team member", f"{RELATORS_BASE_URL}rtm.html")
        RES = ("Researcher", f"{RELATORS_BASE_URL}res.html")
        REV = ("Reviewer", f"{RELATORS_BASE_URL}rev.html")
        RBR = ("Rubricator", f"{RELATORS_BASE_URL}rbr.html")
        RSP = ("Respondent", f"{RELATORS_BASE_URL}rsp.html")
        SCE = ("Scenarist", f"{RELATORS_BASE_URL}sce.html")
        SAD = ("Scientific advisor", f"{RELATORS_BASE_URL}sad.html")
        SCR = ("Scribe", f"{RELATORS_BASE_URL}scr.html")
        SCL = ("Sculptor", f"{RELATORS_BASE_URL}scl.html")
        SDS = ("Sound designer", f"{RELATORS_BASE_URL}sds.html")
        SEC = ("Secretary", f"{RELATORS_BASE_URL}sec.html")
        SLL = ("Seller", f"{RELATORS_BASE_URL}sll.html")
        SGN = ("Signer", f"{RELATORS_BASE_URL}sgn.html")
        SNG = ("Singer", f"{RELATORS_BASE_URL}sng.html")
        SPN = ("Sponsor", f"{RELATORS_BASE_URL}spn.html")
        SPK = ("Speaker", f"{RELATORS_BASE_URL}spk.html")
        STM = ("Stage manager", f"{RELATORS_BASE_URL}stm.html")
        SWD = ("Software developer", f"{RELATORS_BASE_URL}swd.html")
        THS = ("Thesis advisor", f"{RELATORS_BASE_URL}ths.html")
        TRL = ("Translator", f"{RELATORS_BASE_URL}trl.html")
        TYD = ("Type designer", f"{RELATORS_BASE_URL}tyd.html")
        TYG = ("Typographer", f"{RELATORS_BASE_URL}tyg.html")
        VOC = ("Vocalist", "Discontinued code")
        WDE = ("Wood-engraver", f"{RELATORS_BASE_URL}wde.html")
        WAM = ("Writer of accompanying material", f"{RELATORS_BASE_URL}wam.html")
        WIT = ("Witness", f"{RELATORS_BASE_URL}wit.html")

        UNKNOWN = ("Unknown", "Unknown")

        def __init__(self, role, url):
            self._role = role
            self._url = url

        def loc_name(self):
            """
            Define a property to return the name of the role
            """
            return self._role

        def loc_url(self):
            """
            Define a property to return the URL of the role
            """
            return self._url

    @classmethod
    def get_name(cls, role_code):
        """
        Get the name for a given role code
        """
        try:
            return cls.LOCAuthorRoles[role_code].loc_name()
        except KeyError:
            return "Unknown"

    @classmethod
    def get_url(cls, role_code):
        """
        Get the URL for a given role code
        """
        try:
            return cls.LOCAuthorRoles[role_code].loc_url()
        except KeyError:
            return ""

    __tablename__ = "contributions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    rank: Mapped[int] = mapped_column(nullable=True)

    contributor_id: Mapped[int] = mapped_column(
        ForeignKey("contributors.id"), index=True
    )
    contributor: Mapped["app.db.models.contributor.Contributor"] = relationship(
        "app.db.models.contributor.Contributor",
        lazy="joined",
        cascade="all",
    )

    reference_id: Mapped[int] = mapped_column(ForeignKey("references.id"), index=True)
    reference: Mapped["app.db.models.reference.Reference"] = relationship(
        "app.db.models.reference.Reference",
        back_populates="contributions",
        lazy="raise",
    )

    role: Mapped[str] = mapped_column(
        nullable=False, index=True, default=lambda: Contribution.get_url("UNKNOWN")
    )

    affiliations: Mapped[List["app.db.models.organization.Organization"]] = (
        relationship(
            "app.db.models.organization.Organization",
            secondary=affiliations_table,
            lazy="joined",
        )
    )

    @validates("role")
    def validate_role(self, _, role_uri):
        """
        Validate that the role is a valid LOCAuthorRoles enum value
        """
        if not any(role_uri == role.loc_url() for role in Contribution.LOCAuthorRoles):
            raise ValueError(
                f"Unknown role: {role_uri} for reference {self.reference_id}"
            )
        return role_uri


# # Example usage of LOCAuthorRoles enum class:
# print(Contribution.LOCAuthorRoles.AUT.loc_name())  # Output: "Author"
# print(Contribution.LOCAuthorRoles.AUT.loc_url())
# Output: "https://id.loc.gov/vocabulary/relators/aut.html"

# print(Contribution.get_name("AUT"))  # Output: "Author"
# print(Contribution.get_url("AUT"))  # Output: "https://id.loc.gov/vocabulary/relators/aut.html"
